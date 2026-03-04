from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
from PIL import Image

from cad_image_cropper.detectors.border_detector import BorderDetector
from cad_image_cropper.exceptions import CadImageCropperError, InvalidImageError
from cad_image_cropper.models.crop_region import CropRegion
from cad_image_cropper.models.detection_method import DetectionMethod
from cad_image_cropper.models.detection_result import DetectionResult
from cad_image_cropper.models.image_metadata import ImageMetadata
from cad_image_cropper.models.processing_result import ProcessingResult
from cad_image_cropper.models.processing_status import ProcessingStatus
from cad_image_cropper.services.image_cropper import ImageCropper
from cad_image_cropper.services.image_exporter import ImageExporter
from cad_image_cropper.services.image_loader import ImageLoader


class ImageProcessor:
    def __init__(
        self,
        detector: BorderDetector,
        loader: ImageLoader,
        cropper: ImageCropper,
        exporter: ImageExporter,
        output_dir: Path,
    ) -> None:
        self._detector = detector
        self._loader = loader
        self._cropper = cropper
        self._exporter = exporter
        self._output_dir = output_dir

    def process_image(self, file_path: Path, output_dir: Path | None = None) -> ProcessingResult:
        effective_output = output_dir if output_dir is not None else self._output_dir
        try:
            metadata, img = self._load(file_path)
        except InvalidImageError as exc:
            return ProcessingResult(
                input_path=file_path,
                output_path=None,
                status=ProcessingStatus.SKIPPED_CORRUPT,
                warning_message=str(exc),
                detection_method=DetectionMethod.NONE,
            )
        image_array = self._to_array(img)
        detection = self._detect(metadata, image_array)
        if detection.method == DetectionMethod.NONE:
            return ProcessingResult(
                input_path=file_path,
                output_path=None,
                status=ProcessingStatus.SKIPPED_NO_BORDER,
                warning_message=f"No border detected in {file_path.name}",
                detection_method=DetectionMethod.NONE,
            )
        region = self._build_crop_region(detection, metadata)
        try:
            cropped = self._crop(img, region)
            output_path = self._export(cropped, metadata, effective_output)
        except CadImageCropperError as exc:
            return ProcessingResult(
                input_path=file_path,
                output_path=None,
                status=ProcessingStatus.FAILED,
                warning_message=str(exc),
                detection_method=detection.method,
            )
        return ProcessingResult(
            input_path=file_path,
            output_path=output_path,
            status=ProcessingStatus.SUCCESS,
            warning_message=None,
            detection_method=detection.method,
        )

    def _load(self, file_path: Path) -> tuple[ImageMetadata, Image.Image]:
        return self._loader.load_image(file_path)

    def _to_array(self, img: Image.Image) -> npt.NDArray[Any]:
        return np.array(img)

    def _detect(
        self, metadata: ImageMetadata, image_array: npt.NDArray[Any]
    ) -> DetectionResult:
        return self._detector.detect_border(metadata, image_array)

    def _build_crop_region(
        self, detection: DetectionResult, metadata: ImageMetadata
    ) -> CropRegion:
        return CropRegion(
            x_start=0,
            x_end=detection.x_coordinate or metadata.width,
            y_start=0,
            y_end=metadata.height,
        )

    def _crop(self, img: Image.Image, region: CropRegion) -> Image.Image:
        return self._cropper.crop_image(img, region)

    def _export(self, cropped: Image.Image, metadata: ImageMetadata, output_dir: Path) -> Path:
        return self._exporter.export_image(cropped, metadata, output_dir)
