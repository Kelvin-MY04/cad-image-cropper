from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TextColumn

load_dotenv()

from cad_image_cropper.constants import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR
from cad_image_cropper.detectors.border_detector import BorderDetector
from cad_image_cropper.exceptions import ModelLoadError
from cad_image_cropper.models.processing_status import ProcessingStatus
from cad_image_cropper.services.batch_processor import BatchProcessor
from cad_image_cropper.services.image_cropper import ImageCropper
from cad_image_cropper.services.image_exporter import ImageExporter
from cad_image_cropper.services.image_loader import ImageLoader
from cad_image_cropper.services.image_processor import ImageProcessor

app = typer.Typer()


def _build_processor(output_dir: Path) -> tuple[ImageProcessor, bool]:
    from cad_image_cropper.detectors.classical_detector import ClassicalBorderDetector
    from cad_image_cropper.detectors.sam_detector import SamBorderDetector
    from cad_image_cropper.detectors.two_stage_detector import TwoStageDetector

    sam_failed = False
    detector: BorderDetector
    try:
        sam = SamBorderDetector()
        detector = TwoStageDetector(primary=ClassicalBorderDetector(), fallback=sam)
    except ModelLoadError:
        typer.echo(
            "WARNING: HuggingFace model could not be loaded"
            " — running in classical detection mode only.",
            err=True,
        )
        detector = ClassicalBorderDetector()
        sam_failed = True

    processor = ImageProcessor(
        detector=detector,
        loader=ImageLoader(),
        cropper=ImageCropper(),
        exporter=ImageExporter(),
        output_dir=output_dir,
    )
    return processor, sam_failed


@app.command()
def crop(
    input_path: Path | None = typer.Argument(
        None, help=f"PNG file or directory of PNG files (default: {DEFAULT_INPUT_DIR})"
    ),
    output_dir: Path | None = typer.Option(
        DEFAULT_OUTPUT_DIR, "--output-dir", "-o", help="Output directory"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Print per-file OK lines"),
) -> None:
    resolved_input = input_path if input_path is not None else DEFAULT_INPUT_DIR
    resolved_output = output_dir if output_dir is not None else DEFAULT_OUTPUT_DIR

    if not resolved_input.exists():
        typer.echo(f"ERROR: {resolved_input} does not exist.", err=True)
        raise typer.Exit(code=1)

    processor, _ = _build_processor(resolved_output)

    if resolved_input.is_dir():
        _run_batch(processor, resolved_input, resolved_output, verbose)
    else:
        _run_single(processor, resolved_input, resolved_output, verbose)


def _run_single(
    processor: ImageProcessor,
    input_path: Path,
    output_dir: Path,
    verbose: bool,
) -> None:
    result = processor.process_image(input_path)
    if result.status == ProcessingStatus.SUCCESS:
        if verbose:
            typer.echo(f"OK: {input_path.name} -> {result.output_path}")
    elif result.status == ProcessingStatus.SKIPPED_NO_BORDER:
        typer.echo(
            f"WARNING: No border detected in {input_path.name} — skipped.", err=True
        )
    elif result.status == ProcessingStatus.SKIPPED_CORRUPT:
        typer.echo(
            f"WARNING: Could not open {input_path.name} as a valid PNG — skipped.",
            err=True,
        )
    else:
        typer.echo(
            f"ERROR: {input_path.name} failed — {result.warning_message}.", err=True
        )


def _run_batch(
    processor: ImageProcessor,
    input_path: Path,
    output_dir: Path,
    verbose: bool,
) -> None:
    batch = BatchProcessor(processor)
    files = batch.collect_png_files(input_path)

    if not files:
        typer.echo(f"No PNG files found in {input_path}.")
        return

    processed = skipped = failed = 0
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("{task.completed}/{task.total}"),
    ) as progress:
        task = progress.add_task("Processing...", total=len(files))
        results = []
        for f in files:
            progress.update(task, description=f.name)
            results.append(
                processor.process_image(
                    f,
                    output_dir / f.relative_to(input_path).parent,
                )
            )
            progress.advance(task)

    for result in results:
        if result.status == ProcessingStatus.SUCCESS:
            processed += 1
            if verbose:
                typer.echo(f"OK: {result.input_path.name} -> {result.output_path}")
        elif result.status in (
            ProcessingStatus.SKIPPED_NO_BORDER,
            ProcessingStatus.SKIPPED_CORRUPT,
        ):
            skipped += 1
            typer.echo(f"WARNING: {result.warning_message}", err=True)
        else:
            failed += 1
            typer.echo(
                f"ERROR: {result.input_path.name} failed — {result.warning_message}.",
                err=True,
            )

    typer.echo(f"Processed: {processed} | Skipped: {skipped} | Failed: {failed}")
