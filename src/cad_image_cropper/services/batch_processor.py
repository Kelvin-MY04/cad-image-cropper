from pathlib import Path

from cad_image_cropper.models.processing_result import ProcessingResult
from cad_image_cropper.services.image_processor import ImageProcessor


class BatchProcessor:
    def __init__(self, processor: ImageProcessor) -> None:
        self._processor = processor

    def process_directory(
        self, input_dir: Path, output_base: Path | None = None
    ) -> list[ProcessingResult]:
        if not input_dir.is_dir():
            raise FileNotFoundError(
                f"{input_dir} is not a directory"
            )
        files = self.collect_png_files(input_dir)
        return [
            self._processor.process_image(
                f,
                output_base / f.relative_to(input_dir).parent
                if output_base is not None
                else None,
            )
            for f in files
        ]

    def collect_png_files(self, input_dir: Path) -> list[Path]:
        return sorted(
            p for p in input_dir.rglob("*")
            if p.is_file() and p.suffix.lower() == ".png"
        )
