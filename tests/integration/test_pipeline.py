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


def _create_two_panel_png(
    path: Path,
    width: int = 1200,
    height: int = 800,
    stripe_x: int = 600,
    dpi: tuple[float, float] = (150.0, 150.0),
) -> None:
    arr = np.ones((height, width, 3), dtype=np.uint8) * 240
    arr[:, stripe_x - 3 : stripe_x + 3, :] = 10
    img = Image.fromarray(arr, "RGB")
    img.save(path, format="PNG", dpi=dpi)


class TestFullPipeline:
    def test_single_image_crop(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_file = tmp_path / "plan.png"
            output_dir = tmp_path / "output"
            _create_two_panel_png(input_file, stripe_x=600, dpi=(150.0, 150.0))

            processor = ImageProcessor(
                detector=ClassicalBorderDetector(),
                loader=ImageLoader(),
                cropper=ImageCropper(),
                exporter=ImageExporter(),
                output_dir=output_dir,
            )
            result = processor.process_image(input_file)

            assert result.status == ProcessingStatus.SUCCESS
            assert result.output_path is not None
            assert result.output_path.exists()

            out_img = Image.open(result.output_path)
            assert out_img.width <= 620
            assert out_img.height == 800
            loaded_dpi = out_img.info.get("dpi")
            assert loaded_dpi is not None
            assert loaded_dpi[0] == pytest.approx(150.0, abs=0.1)
            assert loaded_dpi[1] == pytest.approx(150.0, abs=0.1)

    def test_no_border_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_file = tmp_path / "blank.png"
            output_dir = tmp_path / "output"
            img = Image.new("RGB", (1200, 800), color=(240, 240, 240))
            img.save(input_file, format="PNG")

            processor = ImageProcessor(
                detector=ClassicalBorderDetector(),
                loader=ImageLoader(),
                cropper=ImageCropper(),
                exporter=ImageExporter(),
                output_dir=output_dir,
            )
            result = processor.process_image(input_file)
            assert result.status == ProcessingStatus.SKIPPED_NO_BORDER
            assert result.output_path is None
