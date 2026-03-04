from pathlib import Path

from PIL import Image

from cad_image_cropper.exceptions import ExportError
from cad_image_cropper.models.image_metadata import ImageMetadata


class ImageExporter:
    def export_image(
        self, image: Image.Image, metadata: ImageMetadata, output_dir: Path
    ) -> Path:
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            raise ExportError(
                f"Cannot create output directory {output_dir}: {exc}", output_dir
            ) from exc
        output_path = self._resolve_output_path(
            output_dir, metadata.file_path.stem, metadata.file_path.suffix
        )
        if output_path.resolve() == metadata.file_path.resolve():
            raise ExportError(
                f"Output path {output_path} would overwrite input file", output_path
            )
        self._write_png(image, output_path, metadata.dpi)
        return output_path

    def _resolve_output_path(
        self, output_dir: Path, stem: str, suffix: str
    ) -> Path:
        candidate = output_dir / f"{stem}{suffix}"
        if not candidate.exists():
            return candidate
        counter = 1
        while True:
            candidate = output_dir / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate
            counter += 1

    def _write_png(
        self,
        image: Image.Image,
        output_path: Path,
        dpi: tuple[float, float] | None,
    ) -> None:
        try:
            if dpi is not None:
                image.save(output_path, format="PNG", dpi=dpi)
            else:
                image.save(output_path, format="PNG")
        except Exception as exc:
            raise ExportError(
                f"Failed to write PNG to {output_path}: {exc}", output_path
            ) from exc
