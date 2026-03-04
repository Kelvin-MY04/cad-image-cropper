from abc import ABC, abstractmethod
from typing import Any

import numpy.typing as npt

from cad_image_cropper.models.detection_result import DetectionResult
from cad_image_cropper.models.image_metadata import ImageMetadata


class BorderDetector(ABC):
    @abstractmethod
    def detect_border(
        self, metadata: ImageMetadata, image_array: npt.NDArray[Any]
    ) -> DetectionResult:
        ...
