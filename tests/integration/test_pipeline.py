import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from cad_image_cropper.detectors.classical_detector import ClassicalBorderDetector
from cad_image_cropper.models.processing_status import ProcessingStatus
from cad_image_cropper.services.image_cropper import ImageCropper
from cad_image_cropper.services.image_exporter import ImageExporter
from cad_image_cropper.services.image_loader import ImageLoader
from cad_image_cropper.services.image_processor import ImageProcessor


def _create_bordered_panel_png(
    path: Path,
    width: int = 1200,
    height: int = 800,
    panel_x: int = 50,
    panel_y: int = 50,
    panel_w: int = 700,
    panel_h: int = 500,
    border_thickness: int = 8,
    dpi: tuple[float, float] = (150.0, 150.0),
) -> None:
    arr = np.ones((height, width, 3), dtype=np.uint8) * 255
    arr[panel_y : panel_y + border_thickness, panel_x : panel_x + panel_w, :] = 0
    bot = panel_y + panel_h
    right = panel_x + panel_w
    arr[bot - border_thickness : bot, panel_x : right, :] = 0
    arr[panel_y : bot, panel_x : panel_x + border_thickness, :] = 0
    arr[panel_y : bot, right - border_thickness : right, :] = 0
    img = Image.fromarray(arr, "RGB")
    img.save(path, format="PNG", dpi=dpi)


def _make_processor(output_dir: Path) -> ImageProcessor:
    return ImageProcessor(
        detector=ClassicalBorderDetector(),
        loader=ImageLoader(),
        cropper=ImageCropper(),
        exporter=ImageExporter(),
        output_dir=output_dir,
    )


class TestFullPipeline:
    def test_single_image_crop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_file = tmp_path / "plan.png"
            output_dir = tmp_path / "output"
            _create_bordered_panel_png(
                input_file, panel_w=700, panel_h=500, dpi=(150.0, 150.0)
            )

            result = _make_processor(output_dir).process_image(input_file)

            assert result.status == ProcessingStatus.SUCCESS
            assert result.output_path is not None
            assert result.output_path.exists()

            out_img = Image.open(result.output_path)
            assert abs(out_img.width - 700) <= 10
            assert abs(out_img.height - 500) <= 10
            loaded_dpi = out_img.info.get("dpi")
            assert loaded_dpi is not None
            assert loaded_dpi[0] == pytest.approx(150.0, abs=0.1)
            assert loaded_dpi[1] == pytest.approx(150.0, abs=0.1)

    def test_no_border_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_file = tmp_path / "blank.png"
            output_dir = tmp_path / "output"
            img = Image.new("RGB", (1200, 800), color=(255, 255, 255))
            img.save(input_file, format="PNG")

            result = _make_processor(output_dir).process_image(input_file)
            assert result.status == ProcessingStatus.SKIPPED_NO_BORDER
            assert result.output_path is None

    def test_sample_image_crops_title_block(self) -> None:
        sample_input = Path("test/sample/input.png")
        if not sample_input.exists():
            pytest.skip("Sample image not available")

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "output"
            result = _make_processor(output_dir).process_image(sample_input)

            assert result.status == ProcessingStatus.SUCCESS
            assert result.output_path is not None

            input_width = Image.open(sample_input).width
            actual_width = Image.open(result.output_path).width
            assert input_width * 0.70 <= actual_width <= input_width * 0.95
