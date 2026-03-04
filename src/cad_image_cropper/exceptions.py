from pathlib import Path


class CadImageCropperError(Exception):
    def __init__(self, message: str, file_path: Path) -> None:
        super().__init__(message)
        self.message = message
        self.file_path = file_path


class InvalidImageError(CadImageCropperError):
    def __init__(self, message: str, file_path: Path) -> None:
        super().__init__(message, file_path)


class BorderDetectionError(CadImageCropperError):
    def __init__(self, message: str, file_path: Path) -> None:
        super().__init__(message, file_path)


class ModelLoadError(CadImageCropperError):
    def __init__(self, message: str, file_path: Path) -> None:
        super().__init__(message, file_path)


class ExportError(CadImageCropperError):
    def __init__(self, message: str, file_path: Path) -> None:
        super().__init__(message, file_path)
