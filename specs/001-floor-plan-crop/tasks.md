---
description: "Task list for CAD Floor Plan Panel Crop implementation"
---

# Tasks: CAD Floor Plan Panel Crop

**Input**: Design documents from `/specs/001-floor-plan-crop/`
**Prerequisites**: plan.md ✅ spec.md ✅ data-model.md ✅ contracts/cli-contract.md ✅ research.md ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and
testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- All file paths are relative to the repository root

---

## Phase 1: Setup

**Purpose**: Project initialization and environment configuration

- [X] T001 Initialize uv project: create `pyproject.toml` with `requires-python = ">=3.12"`, dependencies (pillow>=11, opencv-python-headless>=4.10, transformers>=4.40, torch>=2.4, numpy>=2.1, typer>=0.12), dev dependencies (pytest, ruff, mypy), and `[project.scripts] cad-crop = "cad_image_cropper.cli:app"`
- [X] T002 Create `.python-version` file at repository root containing `3.12`
- [X] T003 [P] Create source directory tree: `src/cad_image_cropper/`, `src/cad_image_cropper/models/`, `src/cad_image_cropper/detectors/`, `src/cad_image_cropper/services/` with `__init__.py` in each
- [X] T004 [P] Create test directory tree: `tests/unit/`, `tests/integration/`, `tests/contract/` with `__init__.py` in each and a root `tests/conftest.py`
- [X] T005 [P] Configure `ruff` in `pyproject.toml`: `target-version = "py312"`, `line-length = 100`, `select = ["E", "F", "I", "N", "UP"]`
- [X] T006 [P] Configure `mypy` in `pyproject.toml`: `python_version = "3.12"`, `strict = true`, `files = ["src"]`

**Checkpoint**: `uv sync` completes without error; `uv run cad-crop --help` is not yet functional but environment is ready

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure that all user stories depend on. No user story work can begin until this phase is complete.

- [X] T007 [P] Create `src/cad_image_cropper/constants.py` with module-level constants: `DEFAULT_INPUT_DIR = Path("/import")`, `DEFAULT_OUTPUT_DIR = Path("/export")`, `SAM_MODEL_ID = "facebook/sam-vit-base"`, `SAM_CONFIDENCE_THRESHOLD = 0.75`, `HOUGH_THRESHOLD = 100`, `HOUGH_MIN_LINE_LENGTH_RATIO = 0.5`, `HOUGH_MAX_LINE_GAP = 20`, `HOUGH_ANGLE_TOLERANCE_PX = 5`
- [X] T008 [P] Create `src/cad_image_cropper/exceptions.py` with `CadImageCropperError(Exception)` base class and four subclasses: `InvalidImageError`, `BorderDetectionError`, `ModelLoadError`, `ExportError` — each accepting `message: str` and `file_path: Path` in `__init__`
- [X] T009 [P] Create `src/cad_image_cropper/models/detection_method.py` with `DetectionMethod(Enum)`: values `MODEL_SAM`, `CLASSICAL`, `NONE`
- [X] T010 [P] Create `src/cad_image_cropper/models/processing_status.py` with `ProcessingStatus(Enum)`: values `SUCCESS`, `SKIPPED_NO_BORDER`, `SKIPPED_CORRUPT`, `FAILED`
- [X] T011 [P] Create `src/cad_image_cropper/models/image_metadata.py` with `ImageMetadata` frozen dataclass: fields `file_path: Path`, `width: int`, `height: int`, `dpi: tuple[float, float] | None`, `color_mode: str`; validate `width > 0`, `height > 0`, `.png` extension in `__post_init__` raising `InvalidImageError`
- [X] T012 [P] Create `src/cad_image_cropper/models/detection_result.py` with `DetectionResult` frozen dataclass: fields `x_coordinate: int | None`, `confidence: float | None`, `method: DetectionMethod`; validate invariants (NONE → x_coordinate is None; MODEL_SAM → confidence present) in `__post_init__`
- [X] T013 [P] Create `src/cad_image_cropper/models/crop_region.py` with `CropRegion` frozen dataclass: fields `x_start: int`, `x_end: int`, `y_start: int`, `y_end: int`; validate `x_end > x_start` and `y_end > y_start` in `__post_init__`
- [X] T014 [P] Create `src/cad_image_cropper/models/processing_result.py` with `ProcessingResult` frozen dataclass: fields `input_path: Path`, `output_path: Path | None`, `status: ProcessingStatus`, `warning_message: str | None`, `detection_method: DetectionMethod`
- [X] T015 Create `src/cad_image_cropper/detectors/border_detector.py` with `BorderDetector(ABC)` abstract class; single abstract method `detect_border(self, metadata: ImageMetadata, image_array: np.ndarray) -> DetectionResult`; import numpy as np (depends on T011, T012)

**Checkpoint**: Foundation complete — `uv run mypy src/` passes on models, exceptions, constants, and ABC

---

## Phase 3: User Story 1 — Single Image Panel Crop (Priority: P1) 🎯 MVP

**Goal**: Process a single PNG file, detect the vertical border, crop the left region, export with DPI preserved.

**Independent Test**: `uv run cad-crop /import/sample.png` → `/export/sample.png` contains only the left panel with DPI metadata matching input.

### Implementation for User Story 1

- [X] T016 [P] [US1] Implement `ClassicalBorderDetector(BorderDetector)` in `src/cad_image_cropper/detectors/classical_detector.py`: methods `detect_border()` (public, orchestrates), `_convert_to_grayscale_array()`, `_apply_vertical_morphology()`, `_apply_binary_threshold()`, `_run_hough_lines()`, `_filter_vertical_lines()`, `_cluster_and_select_dominant_x()`; use constants from `constants.py`; wrap all numpy/cv2 calls in try/except raising `BorderDetectionError`
- [X] T017 [P] [US1] Implement `SamBorderDetector(BorderDetector)` in `src/cad_image_cropper/detectors/sam_detector.py`: `__init__(self)` loads `SamModel` and `SamProcessor` from `SAM_MODEL_ID` in try/except raising `ModelLoadError`; method `detect_border()` runs prompted SAM inference using the approximate x from `_estimate_x_by_column_darkness()`; method `_extract_x_from_mask()` projects mask columns; method `_is_high_confidence()` checks score vs `SAM_CONFIDENCE_THRESHOLD`; all torch/transformers calls wrapped in try/except
- [X] T018 [US1] Implement `TwoStageDetector(BorderDetector)` in `src/cad_image_cropper/detectors/two_stage_detector.py`: `__init__(self, primary: BorderDetector, fallback: BorderDetector)`; `detect_border()` calls primary, checks if result is high-confidence SAM or valid classical result, falls back to `fallback.detect_border()` if not; `_is_result_sufficient()` encapsulates the confidence check logic (depends on T016, T017)
- [X] T019 [P] [US1] Implement `ImageLoader` in `src/cad_image_cropper/services/image_loader.py`: single public method `load_image(file_path: Path) -> tuple[ImageMetadata, Image.Image]`; opens with Pillow in try/except raising `InvalidImageError`; validates `.png` extension; captures `img.info.get("dpi")` before returning; private `_build_metadata()` constructs `ImageMetadata`
- [X] T020 [P] [US1] Implement `ImageCropper` in `src/cad_image_cropper/services/image_cropper.py`: single public method `crop_image(image: Image.Image, region: CropRegion) -> Image.Image`; uses `image.crop((region.x_start, region.y_start, region.x_end, region.y_end))`; private `_build_crop_box()` constructs the tuple; wraps in try/except raising `ExportError`
- [X] T021 [P] [US1] Implement `ImageExporter` in `src/cad_image_cropper/services/image_exporter.py`: public method `export_image(image: Image.Image, metadata: ImageMetadata, output_dir: Path) -> Path`; private `_resolve_output_path(output_dir: Path, stem: str, suffix: str) -> Path` implements the incrementing numeric suffix collision rule; private `_write_png(image: Image.Image, output_path: Path, dpi: tuple[float, float] | None)` calls `image.save(output_path, format="PNG", dpi=dpi)` if dpi present; wraps file I/O in try/except raising `ExportError`
- [X] T022 [US1] Implement `ImageProcessor` in `src/cad_image_cropper/services/image_processor.py`: `__init__(self, detector: BorderDetector, loader: ImageLoader, cropper: ImageCropper, exporter: ImageExporter, output_dir: Path)`; public method `process_image(file_path: Path) -> ProcessingResult`; private methods `_load()`, `_detect()`, `_build_crop_region()`, `_crop()`, `_export()` each handle one step and return the appropriate result or raise; orchestration only in `process_image()` (depends on T015–T021)
- [X] T023 [US1] Implement single-file CLI command in `src/cad_image_cropper/cli.py` using Typer: `app = typer.Typer()`; `@app.command() def crop(input_path: Path, output_dir: Optional[Path] = ..., verbose: bool = False)`; constructs `ImageProcessor` with `TwoStageDetector(SamBorderDetector(), ClassicalBorderDetector())` and `output_dir or DEFAULT_OUTPUT_DIR`; dispatches to `process_image()` for single file; emits warnings to stderr for non-SUCCESS results; exits with code 1 on `INPUT_PATH` not found (depends on T022)

**Checkpoint**: `uv run cad-crop /import/sample.png` produces a correctly cropped PNG in `/export/` with matching DPI — User Story 1 fully functional

---

## Phase 4: User Story 2 — Batch Processing (Priority: P2)

**Goal**: Process all PNG files in a directory in a single invocation; continue on per-file failures.

**Independent Test**: `uv run cad-crop /import/` with a directory of 5 PNGs → 5 output files in `/export/`, plus one skipped file (no border) emits a warning and produces no output for that file.

### Implementation for User Story 2

- [X] T024 [US2] Implement `BatchProcessor` in `src/cad_image_cropper/services/batch_processor.py`: `__init__(self, processor: ImageProcessor)`; public method `process_directory(input_dir: Path) -> list[ProcessingResult]`; private `_collect_png_files(input_dir: Path) -> list[Path]` globs `*.png` case-insensitively; iterates files, calls `processor.process_image()` per file, collects all `ProcessingResult`s; raises `InvalidImageError` if input_dir is not a directory (depends on T022)
- [X] T025 [US2] Extend `crop()` in `src/cad_image_cropper/cli.py` to detect when `input_path` is a directory: construct `BatchProcessor(image_processor)` and call `process_directory()`; emit per-file warnings to stderr for all non-SUCCESS results; print batch summary line `Processed: N | Skipped: N | Failed: N` to stdout after all files are processed (depends on T024)
- [X] T026 [US2] Add `--verbose` flag handling in `src/cad_image_cropper/cli.py`: when `--verbose` is set, print `OK: {filename} -> {output_path}` to stdout for each SUCCESS result in both single-file and batch modes (depends on T025)

**Checkpoint**: `uv run cad-crop /import/` processes all PNGs, prints summary, skips-with-warning on undetectable files — User Story 2 fully functional independently

---

## Phase 5: User Story 3 — Output Path Control (Priority: P3)

**Goal**: Allow the user to specify a custom output directory; auto-create it if missing.

**Independent Test**: `uv run cad-crop /import/sample.png --output-dir /tmp/results` → file appears in `/tmp/results/`; if `/tmp/results` did not exist, it was created; `/import/sample.png` is unmodified.

### Implementation for User Story 3

- [X] T027 [US3] Add output directory auto-creation in `ImageExporter.export_image()` in `src/cad_image_cropper/services/image_exporter.py`: call `output_dir.mkdir(parents=True, exist_ok=True)` wrapped in try/except raising `ExportError` with path context before any file write (depends on T021)
- [X] T028 [US3] Wire `--output-dir` option default to `DEFAULT_OUTPUT_DIR` and `--input-dir` option default to `DEFAULT_INPUT_DIR` in `src/cad_image_cropper/cli.py`: ensure `Optional[Path]` annotation with `typer.Option(DEFAULT_OUTPUT_DIR, ...)` so the defaults appear in `--help` output; validate that `--output-dir` resolved path is not inside the input path to prevent overwrite (depends on T023)
- [X] T029 [US3] Add FR-011 guard in `ImageExporter._resolve_output_path()` in `src/cad_image_cropper/services/image_exporter.py`: raise `ExportError` with descriptive message if resolved output path equals the input file path from `ImageMetadata` (depends on T027)

**Checkpoint**: All three `--output-dir` scenarios from the CLI contract pass — User Stories 1, 2, and 3 all independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Tests, quality gates, and validation

- [X] T030 [P] Write unit tests for all models and exception classes in `tests/unit/test_models.py`: test dataclass field validation (`__post_init__` invariants), enum values, and exception attribute presence
- [X] T031 [P] Write unit tests for `ClassicalBorderDetector` and `TwoStageDetector` in `tests/unit/test_detectors.py`: use synthetic numpy arrays with a dark vertical stripe; assert `DetectionResult.x_coordinate` is within tolerance; test fallback path with a mock SAM detector returning low confidence
- [X] T032 [P] Write unit tests for `ImageLoader`, `ImageCropper`, `ImageExporter`, `ImageProcessor` in `tests/unit/test_services.py`: use `PIL.Image.new()` to create in-memory test images with known DPI; assert output DPI matches; assert `_resolve_output_path()` generates `_1`, `_2` suffixes correctly
- [X] T033 Write integration test in `tests/integration/test_pipeline.py`: create a synthetic two-panel PNG with a dark vertical stripe at x=600; run `ImageProcessor.process_image()`; assert output width equals 600, height unchanged, DPI matches
- [X] T034 Write CLI contract tests using `typer.testing.CliRunner` in `tests/contract/test_cli_contract.py`: test exit code 0 on valid input, exit code 1 on missing input path, exit code 2 on unwritable output dir, stderr warning text for no-border file, batch summary line format
- [X] T035 Run `uv run ruff check src/ tests/` and fix all violations
- [X] T036 Run `uv run mypy src/` and fix all type errors until zero violations under `--strict`
- [X] T037 Run quickstart.md validation checklist: verify each item passes end-to-end against real files in `/import/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Phase 2 — core MVP; blocks Phase 4 and 5
- **User Story 2 (Phase 4)**: Depends on Phase 3 (`ImageProcessor` must exist) — builds on US1
- **User Story 3 (Phase 5)**: Depends on Phase 3 (`ImageExporter` and CLI must exist)
- **Polish (Phase 6)**: Depends on Phases 3–5 all being functionally complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependency on US2 or US3
- **US2 (P2)**: Depends on US1 (`ImageProcessor`) — extends, does not replace
- **US3 (P3)**: Depends on US1 (`ImageExporter`, CLI) — adds option wiring

### Within Each Phase

- All `[P]`-marked tasks within a phase can execute in parallel
- T015 (`BorderDetector` ABC) depends on T011 and T012 (models)
- T018 (`TwoStageDetector`) depends on T016 and T017 (concrete detectors)
- T022 (`ImageProcessor`) depends on T015–T021
- T023 (CLI single-file) depends on T022
- T024 (`BatchProcessor`) depends on T022
- T025 (CLI batch) depends on T024

### Parallel Opportunities

```bash
# Phase 2 — all foundational tasks run in parallel:
T007  T008  T009  T010  T011  T012  T013  T014
# Then T015 after T011 and T012 complete

# Phase 3 — parallel within US1:
T016  T017  T019  T020  T021   (run concurrently)
# Then T018 after T016+T017
# Then T022 after T015+T016+T017+T018+T019+T020+T021
# Then T023 after T022

# Phase 6 — all test writing tasks run in parallel:
T030  T031  T032
# Then T033 after T030–T032
# Then T034 after T033
# Then T035  T036  T037 after T034
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational — CRITICAL, blocks everything
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run `uv run cad-crop /import/sample.png`, verify output
5. Deploy / demo if ready — full value already delivered

### Incremental Delivery

1. Setup + Foundational → environment ready
2. US1 complete → single-image cropping works, demo-able
3. US2 complete → batch processing works, production-ready for directories
4. US3 complete → full path control, workflow-safe
5. Polish → all tests green, linting clean, quickstart validated

### Parallel Team Strategy

With multiple developers after Phase 2:

- Developer A: T016 (`ClassicalBorderDetector`) + T019 (`ImageLoader`)
- Developer B: T017 (`SamBorderDetector`) + T020 (`ImageCropper`) + T021 (`ImageExporter`)
- Merge → T018 (`TwoStageDetector`) → T022 (`ImageProcessor`) → T023 (CLI)

---

## Notes

- `[P]` tasks = different files, no blocking dependencies — safe to parallelize
- `[Story]` label maps each task to a user story for traceability to spec.md acceptance criteria
- Never use `cv2.imread()` or `cv2.imwrite()` — DPI is stripped. Pillow owns all file I/O.
- Capture `img.info.get("dpi")` from the original Pillow image BEFORE calling `img.crop()` — crop does not propagate `info`
- Pass captured `dpi` explicitly to `img.save(..., dpi=dpi)` to write the `pHYs` chunk
- SAM model auto-downloads to `~/.cache/huggingface/hub/` on first `SamBorderDetector.__init__()` call
- If SAM load raises any exception, catch it, emit the `ModelLoadError` warning once via CLI, and fall back to `ClassicalBorderDetector` as the sole detector for the entire run
