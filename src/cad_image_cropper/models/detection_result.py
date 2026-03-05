from dataclasses import dataclass

from cad_image_cropper.models.crop_region import CropRegion
from cad_image_cropper.models.detection_method import DetectionMethod


@dataclass(frozen=True)
class DetectionResult:
    crop_region: CropRegion | None
    confidence: float | None
    method: DetectionMethod

    def __post_init__(self) -> None:
        if self.method == DetectionMethod.NONE and self.crop_region is not None:
            raise ValueError(
                "crop_region must be None when method is NONE"
            )
        if self.method != DetectionMethod.NONE and self.crop_region is None:
            raise ValueError(
                "crop_region must be present when method is not NONE"
            )
        if self.method == DetectionMethod.MODEL_SAM and self.confidence is None:
            raise ValueError(
                "confidence must be present when method is MODEL_SAM"
            )
