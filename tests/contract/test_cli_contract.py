import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
from PIL import Image
from typer.testing import CliRunner

import cad_image_cropper.cli as cli_module
from cad_image_cropper.cli import app
from cad_image_cropper.models.detection_method import DetectionMethod
from cad_image_cropper.models.processing_result import ProcessingResult
from cad_image_cropper.models.processing_status import ProcessingStatus

runner = CliRunner()


def _save_two_panel_png(path: Path) -> None:
    arr = np.ones((400, 600, 3), dtype=np.uint8) * 240
    arr[:, 297:303, :] = 10
    img = Image.fromarray(arr, "RGB")
    img.save(path, format="PNG", dpi=(96.0, 96.0))


class TestCLIContract:
    def test_missing_input_exits_1(self) -> None:
        result = runner.invoke(app, ["/nonexistent/path/image.png"])
        assert result.exit_code == 1

    def test_help_exits_0(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "INPUT_PATH" in result.output

    def test_single_file_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_file = tmp_path / "plan.png"
            output_dir = tmp_path / "out"
            _save_two_panel_png(input_file)

            success_result = ProcessingResult(
                input_path=input_file,
                output_path=output_dir / "plan.png",
                status=ProcessingStatus.SUCCESS,
                warning_message=None,
                detection_method=DetectionMethod.CLASSICAL,
            )
            with patch(
                "cad_image_cropper.cli._build_processor"
            ) as mock_build:
                mock_processor = MagicMock()
                mock_processor.process_image.return_value = success_result
                mock_build.return_value = (mock_processor, False)
                result = runner.invoke(
                    app,
                    [str(input_file), "--output-dir", str(output_dir)],
                )
            assert result.exit_code == 0

    def test_verbose_prints_ok_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_file = tmp_path / "plan.png"
            output_dir = tmp_path / "out"
            _save_two_panel_png(input_file)

            success_result = ProcessingResult(
                input_path=input_file,
                output_path=output_dir / "plan.png",
                status=ProcessingStatus.SUCCESS,
                warning_message=None,
                detection_method=DetectionMethod.CLASSICAL,
            )
            with patch("cad_image_cropper.cli._build_processor") as mock_build:
                mock_processor = MagicMock()
                mock_processor.process_image.return_value = success_result
                mock_build.return_value = (mock_processor, False)
                result = runner.invoke(
                    app,
                    [str(input_file), "--output-dir", str(output_dir), "--verbose"],
                )
            assert "OK:" in result.output

    def test_no_border_emits_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_file = tmp_path / "blank.png"
            output_dir = tmp_path / "out"
            img = Image.new("RGB", (600, 400))
            img.save(input_file, format="PNG")

            skip_result = ProcessingResult(
                input_path=input_file,
                output_path=None,
                status=ProcessingStatus.SKIPPED_NO_BORDER,
                warning_message="No border detected in blank.png",
                detection_method=DetectionMethod.NONE,
            )
            with patch("cad_image_cropper.cli._build_processor") as mock_build:
                mock_processor = MagicMock()
                mock_processor.process_image.return_value = skip_result
                mock_build.return_value = (mock_processor, False)
                result = runner.invoke(
                    app,
                    [str(input_file), "--output-dir", str(output_dir)],
                )
            assert result.exit_code == 0

    def test_batch_summary_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_dir = tmp_path / "input"
            input_dir.mkdir()
            output_dir = tmp_path / "out"
            for i in range(3):
                img = Image.new("RGB", (100, 100))
                img.save(input_dir / f"img{i}.png", format="PNG")

            success_result = ProcessingResult(
                input_path=input_dir / "img0.png",
                output_path=output_dir / "img0.png",
                status=ProcessingStatus.SUCCESS,
                warning_message=None,
                detection_method=DetectionMethod.CLASSICAL,
            )
            with patch("cad_image_cropper.cli._build_processor") as mock_build:
                mock_processor = MagicMock()
                mock_processor.process_image.return_value = success_result
                mock_build.return_value = (mock_processor, False)
                result = runner.invoke(
                    app,
                    [str(input_dir), "--output-dir", str(output_dir)],
                )
            assert "Processed:" in result.output
            assert "Skipped:" in result.output
            assert "Failed:" in result.output

    # T005 [US1] — zero-arg invocation with PNG files in import dir
    def test_zero_args_processes_import_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            import_dir = tmp_path / "import"
            import_dir.mkdir()
            output_dir = tmp_path / "export"
            img_file = import_dir / "plan.png"
            _save_two_panel_png(img_file)

            success_result = ProcessingResult(
                input_path=img_file,
                output_path=output_dir / "plan.png",
                status=ProcessingStatus.SUCCESS,
                warning_message=None,
                detection_method=DetectionMethod.CLASSICAL,
            )
            with (
                patch.object(cli_module, "DEFAULT_INPUT_DIR", import_dir),
                patch("cad_image_cropper.cli._build_processor") as mock_build,
            ):
                mock_processor = MagicMock()
                mock_processor.process_image.return_value = success_result
                mock_build.return_value = (mock_processor, False)
                result = runner.invoke(app, ["--output-dir", str(output_dir)])
            assert result.exit_code == 0
            assert "Processed:" in result.output

    # T006 [US1] — zero-arg invocation on empty import directory
    def test_zero_args_empty_import_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            import_dir = tmp_path / "import"
            import_dir.mkdir()
            output_dir = tmp_path / "export"

            with (
                patch.object(cli_module, "DEFAULT_INPUT_DIR", import_dir),
                patch("cad_image_cropper.cli._build_processor") as mock_build,
            ):
                mock_build.return_value = (MagicMock(), False)
                result = runner.invoke(app, ["--output-dir", str(output_dir)])
            assert result.exit_code == 0
            assert "No PNG files found in" in result.output

    # T007 [US1] — zero-arg invocation with missing import directory
    def test_zero_args_missing_import_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "does_not_exist"
            with patch.object(cli_module, "DEFAULT_INPUT_DIR", missing):
                result = runner.invoke(app, [])
            assert result.exit_code == 1
            assert "does not exist" in result.output

    # T008 [US2] — explicit directory path override still works
    def test_explicit_dir_path_still_works(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_dir = tmp_path / "input"
            input_dir.mkdir()
            output_dir = tmp_path / "out"
            img = Image.new("RGB", (100, 100))
            img.save(input_dir / "img.png", format="PNG")

            success_result = ProcessingResult(
                input_path=input_dir / "img.png",
                output_path=output_dir / "img.png",
                status=ProcessingStatus.SUCCESS,
                warning_message=None,
                detection_method=DetectionMethod.CLASSICAL,
            )
            with patch("cad_image_cropper.cli._build_processor") as mock_build:
                mock_processor = MagicMock()
                mock_processor.process_image.return_value = success_result
                mock_build.return_value = (mock_processor, False)
                result = runner.invoke(
                    app, [str(input_dir), "--output-dir", str(output_dir)]
                )
            assert result.exit_code == 0
            assert "Processed:" in result.output

    # T009 [US2] — explicit single file path override still works
    def test_explicit_file_path_still_works(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_file = tmp_path / "plan.png"
            output_dir = tmp_path / "out"
            _save_two_panel_png(input_file)

            success_result = ProcessingResult(
                input_path=input_file,
                output_path=output_dir / "plan.png",
                status=ProcessingStatus.SUCCESS,
                warning_message=None,
                detection_method=DetectionMethod.CLASSICAL,
            )
            with patch("cad_image_cropper.cli._build_processor") as mock_build:
                mock_processor = MagicMock()
                mock_processor.process_image.return_value = success_result
                mock_build.return_value = (mock_processor, False)
                result = runner.invoke(
                    app, [str(input_file), "--output-dir", str(output_dir)]
                )
            assert result.exit_code == 0
            assert "Processed:" not in result.output

    # T010 [US2] — explicit nonexistent path exits with code 1
    def test_explicit_nonexistent_path_exits_1(self) -> None:
        result = runner.invoke(app, ["/nonexistent/path/that/does/not/exist"])
        assert result.exit_code == 1
        assert "does not exist" in result.output

    # T011 [US3] — --output-dir override writes to custom directory
    def test_output_dir_override_writes_to_custom_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_file = tmp_path / "plan.png"
            custom_output = tmp_path / "custom_out"
            _save_two_panel_png(input_file)

            success_result = ProcessingResult(
                input_path=input_file,
                output_path=custom_output / "plan.png",
                status=ProcessingStatus.SUCCESS,
                warning_message=None,
                detection_method=DetectionMethod.CLASSICAL,
            )
            with patch("cad_image_cropper.cli._build_processor") as mock_build:
                mock_processor = MagicMock()
                mock_processor.process_image.return_value = success_result
                mock_build.return_value = (mock_processor, False)
                result = runner.invoke(
                    app,
                    [str(input_file), "--output-dir", str(custom_output)],
                )
            assert result.exit_code == 0
            mock_build.assert_called_once_with(custom_output)

    # T012 [US3] — output directory is auto-created when absent
    def test_output_dir_autocreated_if_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_file = tmp_path / "plan.png"
            new_output = tmp_path / "new" / "subdir"
            _save_two_panel_png(input_file)

            success_result = ProcessingResult(
                input_path=input_file,
                output_path=new_output / "plan.png",
                status=ProcessingStatus.SUCCESS,
                warning_message=None,
                detection_method=DetectionMethod.CLASSICAL,
            )
            with patch("cad_image_cropper.cli._build_processor") as mock_build:
                mock_processor = MagicMock()
                mock_processor.process_image.return_value = success_result
                mock_build.return_value = (mock_processor, False)
                result = runner.invoke(
                    app,
                    [str(input_file), "--output-dir", str(new_output)],
                )
            assert result.exit_code == 0
            mock_build.assert_called_once_with(new_output)
