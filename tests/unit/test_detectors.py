from pathlib import Path
from unittest.mock import MagicMock

import numpy as np

from cad_image_cropper.detectors.classical_detector import ClassicalBorderDetector
from cad_image_cropper.detectors.two_stage_detector import TwoStageDetector
from cad_image_cropper.models.crop_region import CropRegion
from cad_image_cropper.models.detection_method import DetectionMethod
from cad_image_cropper.models.detection_result import DetectionResult
from cad_image_cropper.models.image_metadata import ImageMetadata


def _make_metadata(width: int = 1000, height: int = 800) -> ImageMetadata:
    return ImageMetadata(
        file_path=Path("test.png"),
        width=width,
        height=height,
        dpi=None,
        color_mode="RGB",
    )


def _make_bold_border_image(
    width: int,
    height: int,
    panel_x: int,
    panel_y: int,
    panel_w: int,
    panel_h: int,
    thickness: int = 8,
) -> np.ndarray:  # type: ignore[type-arg]
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    img[panel_y : panel_y + thickness, panel_x : panel_x + panel_w, :] = 0
    img[panel_y + panel_h - thickness : panel_y + panel_h, panel_x : panel_x + panel_w, :] = 0
    img[panel_y : panel_y + panel_h, panel_x : panel_x + thickness, :] = 0
    img[panel_y : panel_y + panel_h, panel_x + panel_w - thickness : panel_x + panel_w, :] = 0
    return img


class TestClassicalBorderDetector:
    def test_detects_bold_border_rectangle(self) -> None:
        detector = ClassicalBorderDetector()
        metadata = _make_metadata(width=1000, height=800)
        image = _make_bold_border_image(
            width=1000, height=800, panel_x=50, panel_y=100, panel_w=700, panel_h=500
        )
        result = detector.detect_border(metadata, image)
        assert result.method == DetectionMethod.CLASSICAL
        assert result.crop_region is not None
        assert abs(result.crop_region.x_start - 50) <= 10
        assert abs(result.crop_region.x_end - 750) <= 10
        assert abs(result.crop_region.y_start - 100) <= 10
        assert abs(result.crop_region.y_end - 600) <= 10

    def test_rejects_thin_border(self) -> None:
        detector = ClassicalBorderDetector()
        metadata = _make_metadata(width=1000, height=800)
        image = _make_bold_border_image(
            width=1000, height=800, panel_x=50, panel_y=100, panel_w=700, panel_h=500,
            thickness=1,
        )
        result = detector.detect_border(metadata, image)
        assert result.method == DetectionMethod.NONE
        assert result.crop_region is None

    def test_rejects_small_panel(self) -> None:
        detector = ClassicalBorderDetector()
        metadata = _make_metadata(width=1000, height=800)
        image = _make_bold_border_image(
            width=1000, height=800, panel_x=50, panel_y=100, panel_w=300, panel_h=500
        )
        result = detector.detect_border(metadata, image)
        assert result.method == DetectionMethod.NONE
        assert result.crop_region is None

    def test_selects_widest_when_multiple(self) -> None:
        detector = ClassicalBorderDetector()
        metadata = _make_metadata(width=2000, height=1000)
        image = np.ones((1000, 2000, 3), dtype=np.uint8) * 255
        _draw_border(image, x=50, y=100, w=1000, h=600)
        _draw_border(image, x=1100, y=100, w=850, h=600)
        result = detector.detect_border(metadata, image)
        assert result.method == DetectionMethod.CLASSICAL
        assert result.crop_region is not None
        assert abs(result.crop_region.x_start - 50) <= 10
        assert abs(result.crop_region.x_end - 1050) <= 10

    def test_returns_none_for_blank_image(self) -> None:
        detector = ClassicalBorderDetector()
        metadata = _make_metadata(width=1000, height=800)
        image = np.ones((800, 1000, 3), dtype=np.uint8) * 255
        result = detector.detect_border(metadata, image)
        assert result.method == DetectionMethod.NONE
        assert result.crop_region is None


def _draw_border(
    image: np.ndarray,  # type: ignore[type-arg]
    x: int,
    y: int,
    w: int,
    h: int,
    thickness: int = 8,
) -> None:
    image[y : y + thickness, x : x + w, :] = 0
    image[y + h - thickness : y + h, x : x + w, :] = 0
    image[y : y + h, x : x + thickness, :] = 0
    image[y : y + h, x + w - thickness : x + w, :] = 0


class TestTwoStageDetector:
    def test_uses_primary_when_sufficient(self) -> None:
        region = CropRegion(x_start=0, x_end=600, y_start=0, y_end=800)
        primary = MagicMock()
        primary.detect_border.return_value = DetectionResult(
            crop_region=region,
            confidence=None,
            method=DetectionMethod.CLASSICAL,
        )
        fallback = MagicMock()
        detector = TwoStageDetector(primary=primary, fallback=fallback)
        metadata = _make_metadata()
        image = np.zeros((800, 1000, 3), dtype=np.uint8)
        result = detector.detect_border(metadata, image)
        assert result.crop_region == region
        fallback.detect_border.assert_not_called()

    def test_falls_back_when_primary_returns_none(self) -> None:
        fallback_region = CropRegion(x_start=0, x_end=500, y_start=0, y_end=800)
        primary = MagicMock()
        primary.detect_border.return_value = DetectionResult(
            crop_region=None,
            confidence=None,
            method=DetectionMethod.NONE,
        )
        fallback = MagicMock()
        fallback.detect_border.return_value = DetectionResult(
            crop_region=fallback_region,
            confidence=None,
            method=DetectionMethod.CLASSICAL,
        )
        detector = TwoStageDetector(primary=primary, fallback=fallback)
        metadata = _make_metadata()
        image = np.zeros((800, 1000, 3), dtype=np.uint8)
        result = detector.detect_border(metadata, image)
        assert result.crop_region == fallback_region
        fallback.detect_border.assert_called_once()

    def test_falls_back_when_sam_low_confidence(self) -> None:
        region = CropRegion(x_start=0, x_end=600, y_start=0, y_end=800)
        fallback_region = CropRegion(x_start=0, x_end=590, y_start=0, y_end=800)
        primary = MagicMock()
        primary.detect_border.return_value = DetectionResult(
            crop_region=region,
            confidence=0.5,
            method=DetectionMethod.MODEL_SAM,
        )
        fallback = MagicMock()
        fallback.detect_border.return_value = DetectionResult(
            crop_region=fallback_region,
            confidence=None,
            method=DetectionMethod.CLASSICAL,
        )
        detector = TwoStageDetector(primary=primary, fallback=fallback)
        metadata = _make_metadata()
        image = np.zeros((800, 1000, 3), dtype=np.uint8)
        result = detector.detect_border(metadata, image)
        assert result.method == DetectionMethod.CLASSICAL
        fallback.detect_border.assert_called_once()
