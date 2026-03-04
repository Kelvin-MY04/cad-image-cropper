from dataclasses import dataclass
from pathlib import Path

from cad_image_cropper.models.detection_method import DetectionMethod
from cad_image_cropper.models.processing_status import ProcessingStatus


@dataclass(frozen=True)
class ProcessingResult:
    input_path: Path
    output_path: Path | None
    status: ProcessingStatus
    warning_message: str | None
    detection_method: DetectionMethod
