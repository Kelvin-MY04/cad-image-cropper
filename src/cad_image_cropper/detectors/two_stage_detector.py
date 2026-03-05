from typing import Any

import numpy.typing as npt

from cad_image_cropper.constants import SAM_CONFIDENCE_THRESHOLD
from cad_image_cropper.detectors.border_detector import BorderDetector
from cad_image_cropper.models.detection_method import DetectionMethod
from cad_image_cropper.models.detection_result import DetectionResult
from cad_image_cropper.models.image_metadata import ImageMetadata


class TwoStageDetector(BorderDetector):
    def __init__(self, primary: BorderDetector, fallback: BorderDetector) -> None:
        self._primary = primary
        self._fallback = fallback

    def detect_border(
        self, metadata: ImageMetadata, image_array: npt.NDArray[Any]
    ) -> DetectionResult:
        primary_result = self._primary.detect_border(metadata, image_array)
        if self._is_result_sufficient(primary_result):
            return primary_result
        return self._fallback.detect_border(metadata, image_array)

    def _is_result_sufficient(self, result: DetectionResult) -> bool:
        if result.method == DetectionMethod.NONE:
            return False
        if result.method == DetectionMethod.MODEL_SAM:
            return (
                result.confidence is not None
                and result.confidence >= SAM_CONFIDENCE_THRESHOLD
                and result.crop_region is not None
            )
        return result.crop_region is not None
