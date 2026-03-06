from pathlib import Path


class CadImageCropperError(Exception):
    def __init__(self, message: str, file_path: Path) -> None:
        super().__init__(message)
        self.message = message
        self.file_path = file_path


class InvalidImageError(CadImageCropperError):
    pass


class BorderDetectionError(CadImageCropperError):
    pass


class ModelLoadError(CadImageCropperError):
    pass


class ExportError(CadImageCropperError):
    pass
