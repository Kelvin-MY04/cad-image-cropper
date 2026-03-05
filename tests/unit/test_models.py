from pathlib import Path

import pytest

from cad_image_cropper.exceptions import (
    BorderDetectionError,
    CadImageCropperError,
    ExportError,
    InvalidImageError,
    ModelLoadError,
)
from cad_image_cropper.models.crop_region import CropRegion
from cad_image_cropper.models.detection_method import DetectionMethod
from cad_image_cropper.models.detection_result import DetectionResult
from cad_image_cropper.models.image_metadata import ImageMetadata
from cad_image_cropper.models.processing_result import ProcessingResult
from cad_image_cropper.models.processing_status import ProcessingStatus


class TestDetectionMethodEnum:
    def test_values_exist(self) -> None:
        assert DetectionMethod.MODEL_SAM.value == "MODEL_SAM"
        assert DetectionMethod.CLASSICAL.value == "CLASSICAL"
        assert DetectionMethod.NONE.value == "NONE"


class TestProcessingStatusEnum:
    def test_values_exist(self) -> None:
        assert ProcessingStatus.SUCCESS.value == "SUCCESS"
        assert ProcessingStatus.SKIPPED_NO_BORDER.value == "SKIPPED_NO_BORDER"
        assert ProcessingStatus.SKIPPED_CORRUPT.value == "SKIPPED_CORRUPT"
        assert ProcessingStatus.FAILED.value == "FAILED"


class TestImageMetadata:
    def test_valid_creation(self) -> None:
        m = ImageMetadata(
            file_path=Path("test.png"),
            width=100,
            height=200,
            dpi=(96.0, 96.0),
            color_mode="RGB",
        )
        assert m.width == 100
        assert m.height == 200

    def test_invalid_extension_raises(self) -> None:
        with pytest.raises(InvalidImageError):
            ImageMetadata(
                file_path=Path("test.jpg"),
                width=100,
                height=200,
                dpi=None,
                color_mode="RGB",
            )

    def test_zero_width_raises(self) -> None:
        with pytest.raises(InvalidImageError):
            ImageMetadata(
                file_path=Path("test.png"),
                width=0,
                height=200,
                dpi=None,
                color_mode="RGB",
            )

    def test_zero_height_raises(self) -> None:
        with pytest.raises(InvalidImageError):
            ImageMetadata(
                file_path=Path("test.png"),
                width=100,
                height=0,
                dpi=None,
                color_mode="RGB",
            )

    def test_none_dpi_allowed(self) -> None:
        m = ImageMetadata(
            file_path=Path("test.png"),
            width=100,
            height=200,
            dpi=None,
            color_mode="L",
        )
        assert m.dpi is None


class TestDetectionResult:
    def test_detection_result_with_crop_region(self) -> None:
        region = CropRegion(x_start=0, x_end=800, y_start=0, y_end=600)
        r = DetectionResult(crop_region=region, confidence=None, method=DetectionMethod.CLASSICAL)
        assert r.crop_region == region
        assert r.confidence is None

    def test_detection_result_none_has_null_crop_region(self) -> None:
        r = DetectionResult(crop_region=None, confidence=None, method=DetectionMethod.NONE)
        assert r.crop_region is None
        assert r.method == DetectionMethod.NONE

    def test_detection_result_crop_region_required_for_classical(self) -> None:
        with pytest.raises(ValueError):
            DetectionResult(crop_region=None, confidence=None, method=DetectionMethod.CLASSICAL)

    def test_none_with_crop_region_raises(self) -> None:
        region = CropRegion(x_start=0, x_end=800, y_start=0, y_end=600)
        with pytest.raises(ValueError):
            DetectionResult(crop_region=region, confidence=None, method=DetectionMethod.NONE)

    def test_sam_without_confidence_raises(self) -> None:
        region = CropRegion(x_start=0, x_end=800, y_start=0, y_end=600)
        with pytest.raises(ValueError):
            DetectionResult(crop_region=region, confidence=None, method=DetectionMethod.MODEL_SAM)

    def test_sam_result(self) -> None:
        region = CropRegion(x_start=0, x_end=400, y_start=0, y_end=600)
        r = DetectionResult(crop_region=region, confidence=0.9, method=DetectionMethod.MODEL_SAM)
        assert r.confidence == 0.9


class TestCropRegion:
    def test_valid_region(self) -> None:
        r = CropRegion(x_start=0, x_end=500, y_start=0, y_end=800)
        assert r.x_end > r.x_start
        assert r.y_end > r.y_start

    def test_invalid_x_raises(self) -> None:
        with pytest.raises(ValueError):
            CropRegion(x_start=500, x_end=500, y_start=0, y_end=800)

    def test_invalid_y_raises(self) -> None:
        with pytest.raises(ValueError):
            CropRegion(x_start=0, x_end=500, y_start=800, y_end=800)


class TestProcessingResult:
    def test_success_result(self) -> None:
        r = ProcessingResult(
            input_path=Path("in.png"),
            output_path=Path("out.png"),
            status=ProcessingStatus.SUCCESS,
            warning_message=None,
            detection_method=DetectionMethod.CLASSICAL,
        )
        assert r.status == ProcessingStatus.SUCCESS
        assert r.warning_message is None

    def test_skipped_result(self) -> None:
        r = ProcessingResult(
            input_path=Path("in.png"),
            output_path=None,
            status=ProcessingStatus.SKIPPED_NO_BORDER,
            warning_message="No border detected",
            detection_method=DetectionMethod.NONE,
        )
        assert r.output_path is None


class TestExceptionHierarchy:
    def test_all_are_cad_errors(self) -> None:
        p = Path("test.png")
        for cls in (InvalidImageError, BorderDetectionError, ModelLoadError, ExportError):
            exc = cls("msg", p)
            assert isinstance(exc, CadImageCropperError)
            assert exc.message == "msg"
            assert exc.file_path == p
