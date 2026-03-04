from dataclasses import dataclass
from pathlib import Path

from cad_image_cropper.exceptions import InvalidImageError


@dataclass(frozen=True)
class ImageMetadata:
    file_path: Path
    width: int
    height: int
    dpi: tuple[float, float] | None
    color_mode: str

    def __post_init__(self) -> None:
        if self.width <= 0:
            raise InvalidImageError(
                f"Image width must be > 0, got {self.width}", self.file_path
            )
        if self.height <= 0:
            raise InvalidImageError(
                f"Image height must be > 0, got {self.height}", self.file_path
            )
        if self.file_path.suffix.lower() != ".png":
            raise InvalidImageError(
                f"File must have .png extension, got {self.file_path.suffix!r}",
                self.file_path,
            )
