from pathlib import Path
from unittest.mock import MagicMock

import numpy as np

from cad_image_cropper.detectors.classical_detector import ClassicalBorderDetector
from cad_image_cropper.detectors.two_stage_detector import TwoStageDetector
from cad_image_cropper.models.detection_method import DetectionMethod
from cad_image_cropper.models.detection_result import DetectionResult
from cad_image_cropper.models.image_metadata import ImageMetadata


def _make_metadata(width: int = 1200, height: int = 800) -> ImageMetadata:
    return ImageMetadata(
        file_path=Path("test.png"),
        width=width,
        height=height,
        dpi=None,
        color_mode="RGB",
    )


def _make_two_panel_image(width: int = 1200, height: int = 800, stripe_x: int = 600) -> np.ndarray:  # type: ignore[type-arg]
    img = np.ones((height, width, 3), dtype=np.uint8) * 240
    img[:, stripe_x - 3 : stripe_x + 3, :] = 10
    return img


class TestClassicalBorderDetector:
    def test_detects_vertical_stripe(self) -> None:
        detector = ClassicalBorderDetector()
        metadata = _make_metadata()
        image = _make_two_panel_image(stripe_x=600)
        result = detector.detect_border(metadata, image)
        assert result.method == DetectionMethod.CLASSICAL
        assert result.x_coordinate is not None
        assert abs(result.x_coordinate - 600) <= 20

    def test_returns_none_for_blank_image(self) -> None:
        detector = ClassicalBorderDetector()
        metadata = _make_metadata()
        image = np.ones((800, 1200, 3), dtype=np.uint8) * 240
        result = detector.detect_border(metadata, image)
        assert result.method == DetectionMethod.NONE
        assert result.x_coordinate is None


class TestTwoStageDetector:
    def test_uses_primary_when_sufficient(self) -> None:
        primary = MagicMock()
        primary.detect_border.return_value = DetectionResult(
            x_coordinate=600,
            confidence=None,
            method=DetectionMethod.CLASSICAL,
        )
        fallback = MagicMock()
        detector = TwoStageDetector(primary=primary, fallback=fallback)
        metadata = _make_metadata()
        image = np.zeros((800, 1200, 3), dtype=np.uint8)
        result = detector.detect_border(metadata, image)
        assert result.x_coordinate == 600
        fallback.detect_border.assert_not_called()

    def test_falls_back_when_primary_returns_none(self) -> None:
        primary = MagicMock()
        primary.detect_border.return_value = DetectionResult(
            x_coordinate=None,
            confidence=None,
            method=DetectionMethod.NONE,
        )
        fallback = MagicMock()
        fallback.detect_border.return_value = DetectionResult(
            x_coordinate=500,
            confidence=None,
            method=DetectionMethod.CLASSICAL,
        )
        detector = TwoStageDetector(primary=primary, fallback=fallback)
        metadata = _make_metadata()
        image = np.zeros((800, 1200, 3), dtype=np.uint8)
        result = detector.detect_border(metadata, image)
        assert result.x_coordinate == 500
        fallback.detect_border.assert_called_once()

    def test_falls_back_when_sam_low_confidence(self) -> None:
        primary = MagicMock()
        primary.detect_border.return_value = DetectionResult(
            x_coordinate=600,
            confidence=0.5,
            method=DetectionMethod.MODEL_SAM,
        )
        fallback = MagicMock()
        fallback.detect_border.return_value = DetectionResult(
            x_coordinate=590,
            confidence=None,
            method=DetectionMethod.CLASSICAL,
        )
        detector = TwoStageDetector(primary=primary, fallback=fallback)
        metadata = _make_metadata()
        image = np.zeros((800, 1200, 3), dtype=np.uint8)
        result = detector.detect_border(metadata, image)
        assert result.method == DetectionMethod.CLASSICAL
        fallback.detect_border.assert_called_once()
