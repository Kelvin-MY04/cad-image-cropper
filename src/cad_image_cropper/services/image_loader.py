from pathlib import Path

from PIL import Image

from cad_image_cropper.exceptions import InvalidImageError
from cad_image_cropper.models.image_metadata import ImageMetadata


class ImageLoader:
    def load_image(self, file_path: Path) -> tuple[ImageMetadata, Image.Image]:
        if file_path.suffix.lower() != ".png":
            raise InvalidImageError(
                f"File must have .png extension: {file_path}", file_path
            )
        try:
            img = Image.open(file_path)
            img.load()
        except Exception as exc:
            raise InvalidImageError(
                f"Cannot open file as PNG: {exc}", file_path
            ) from exc
        metadata = self._build_metadata(file_path, img)
        return metadata, img

    def _build_metadata(self, file_path: Path, img: Image.Image) -> ImageMetadata:
        raw_dpi = img.info.get("dpi")
        dpi: tuple[float, float] | None = None
        if isinstance(raw_dpi, (tuple, list)) and len(raw_dpi) == 2:
            dpi = (float(raw_dpi[0]), float(raw_dpi[1]))
        return ImageMetadata(
            file_path=file_path,
            width=img.width,
            height=img.height,
            dpi=dpi,
            color_mode=img.mode,
        )
