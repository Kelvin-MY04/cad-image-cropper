import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image
from pytest import approx

from cad_image_cropper.exceptions import InvalidImageError
from cad_image_cropper.models.crop_region import CropRegion
from cad_image_cropper.models.detection_method import DetectionMethod
from cad_image_cropper.models.detection_result import DetectionResult
from cad_image_cropper.models.image_metadata import ImageMetadata
from cad_image_cropper.models.processing_status import ProcessingStatus
from cad_image_cropper.services.image_cropper import ImageCropper
from cad_image_cropper.services.image_exporter import ImageExporter
from cad_image_cropper.services.image_loader import ImageLoader
from cad_image_cropper.services.image_processor import ImageProcessor


def _save_test_png(
    path: Path, width: int = 200, height: int = 100, dpi: tuple[float, float] | None = None
) -> None:
    img = Image.new("RGB", (width, height), color=(200, 200, 200))
    if dpi is not None:
        img.save(path, format="PNG", dpi=dpi)
    else:
        img.save(path, format="PNG")


class TestImageLoader:
    def test_loads_valid_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.png"
            _save_test_png(path, dpi=(96.0, 96.0))
            loader = ImageLoader()
            metadata, img = loader.load_image(path)
            assert metadata.width == 200
            assert metadata.height == 100
            assert metadata.dpi is not None
            assert metadata.dpi[0] == approx(96.0, abs=0.1)
            assert metadata.dpi[1] == approx(96.0, abs=0.1)
            assert metadata.color_mode == "RGB"

    def test_rejects_non_png_extension(self) -> None:
        loader = ImageLoader()
        with pytest.raises(InvalidImageError):
            loader.load_image(Path("test.jpg"))

    def test_rejects_missing_file(self) -> None:
        loader = ImageLoader()
        with pytest.raises(InvalidImageError):
            loader.load_image(Path("/nonexistent/test.png"))

    def test_loads_png_without_dpi(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nodpi.png"
            _save_test_png(path, dpi=None)
            loader = ImageLoader()
            metadata, _ = loader.load_image(path)
            assert metadata.dpi is None


class TestImageCropper:
    def test_crops_to_region(self) -> None:
        img = Image.new("RGB", (200, 100), color=(100, 100, 100))
        region = CropRegion(x_start=0, x_end=100, y_start=0, y_end=100)
        cropper = ImageCropper()
        result = cropper.crop_image(img, region)
        assert result.size == (100, 100)

    def test_crop_preserves_height(self) -> None:
        img = Image.new("RGB", (1200, 800))
        region = CropRegion(x_start=0, x_end=600, y_start=0, y_end=800)
        cropper = ImageCropper()
        result = cropper.crop_image(img, region)
        assert result.height == 800
        assert result.width == 600


class TestImageExporter:
    def test_exports_with_dpi(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            img = Image.new("RGB", (100, 100))
            metadata = ImageMetadata(
                file_path=Path("floor.png"),
                width=100,
                height=100,
                dpi=(150.0, 150.0),
                color_mode="RGB",
            )
            exporter = ImageExporter()
            out_path = exporter.export_image(img, metadata, output_dir)
            assert out_path.exists()
            loaded = Image.open(out_path)
            loaded_dpi = loaded.info.get("dpi")
            assert loaded_dpi is not None
            assert loaded_dpi[0] == approx(150.0, abs=0.1)
            assert loaded_dpi[1] == approx(150.0, abs=0.1)

    def test_collision_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            img = Image.new("RGB", (100, 100))
            metadata = ImageMetadata(
                file_path=Path("floor.png"),
                width=100,
                height=100,
                dpi=None,
                color_mode="RGB",
            )
            exporter = ImageExporter()
            path1 = exporter.export_image(img, metadata, output_dir)
            path2 = exporter.export_image(img, metadata, output_dir)
            path3 = exporter.export_image(img, metadata, output_dir)
            assert path1.name == "floor.png"
            assert path2.name == "floor_1.png"
            assert path3.name == "floor_2.png"

    def test_creates_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "new" / "nested"
            img = Image.new("RGB", (100, 100))
            metadata = ImageMetadata(
                file_path=Path("f.png"),
                width=100,
                height=100,
                dpi=None,
                color_mode="RGB",
            )
            exporter = ImageExporter()
            exporter.export_image(img, metadata, output_dir)
            assert output_dir.is_dir()


class TestImageProcessorCropRegion:
    def test_crop_uses_detection_crop_region(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_file = tmp_path / "plan.png"
            output_dir = tmp_path / "out"
            Image.new("RGB", (1200, 800), color=(240, 240, 240)).save(
                input_file, format="PNG", dpi=(150.0, 150.0)
            )
            region = CropRegion(x_start=0, x_end=900, y_start=0, y_end=800)
            detector = MagicMock()
            detector.detect_border.return_value = DetectionResult(
                crop_region=region, confidence=None, method=DetectionMethod.CLASSICAL
            )
            processor = ImageProcessor(
                detector=detector,
                loader=ImageLoader(),
                cropper=ImageCropper(),
                exporter=ImageExporter(),
                output_dir=output_dir,
            )
            result = processor.process_image(input_file)
            assert result.status == ProcessingStatus.SUCCESS
            assert result.output_path is not None
            out_img = Image.open(result.output_path)
            assert out_img.width == 900
            assert out_img.height == 800
