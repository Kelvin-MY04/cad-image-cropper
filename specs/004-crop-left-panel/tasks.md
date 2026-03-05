---
description: "Task list for feature 004-crop-left-panel"
---

# Tasks: Image Detection and Cropping — Left Panel Border Crop

**Input**: Design documents from `specs/004-crop-left-panel/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new constants required by the contour-based detection algorithm before any other work begins.

- [x] T001 Add 4 BORDER_* constants to `src/cad_image_cropper/constants.py`: `BORDER_OPEN_KERNEL_SIZE = 4`, `BORDER_MIN_HEIGHT_RATIO = 0.50`, `BORDER_MIN_WIDTH_RATIO = 0.40`, `BORDER_APPROX_POLY_EPSILON = 0.02`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Migrate `DetectionResult` from `x_coordinate` to `crop_region` and update all dependents. All user story work depends on this migration.

**⚠️ CRITICAL**: No user story work can begin until T002 is complete. T003 and T004 can run in parallel after T002.

- [x] T002 Update `DetectionResult` in `src/cad_image_cropper/models/detection_result.py` — remove `x_coordinate: int | None`, add `crop_region: CropRegion | None`; update `__post_init__` validation: crop_region must be None when method==NONE and non-None when method!=NONE
- [x] T003 [P] Update `TwoStageDetector._is_result_sufficient` in `src/cad_image_cropper/detectors/two_stage_detector.py` — change `result.x_coordinate is not None` to `result.crop_region is not None`
- [x] T004 [P] Replace `SamBorderDetector._extract_x_from_mask` with `_extract_crop_region_from_mask` in `src/cad_image_cropper/detectors/sam_detector.py` — use `np.where` on row/column axis sums to get min/max y and x, return `CropRegion(x_start, x_end, y_start, y_end)`; update `detect_border` call site
- [x] T005 Update `ImageProcessor._build_crop_region` in `src/cad_image_cropper/services/image_processor.py` — return `detection.crop_region` directly; raise `BorderDetectionError("crop_region is None for non-NONE detection", metadata.file_path)` if None

**Checkpoint**: DetectionResult migration complete — user story implementation can now begin

---

## Phase 3: User Story 1 — Detect and Crop to Main Drawing Panel (Priority: P1) 🎯 MVP

**Goal**: Detect the main drawing panel in a CAD floor plan image by its thick black rectangular border, using contour-based detection (morphological opening + Otsu threshold + findContours + approxPolyDP).

**Independent Test**: Process a synthetic PNG with an 8px black rectangle spanning ≥40% width and ≥50% height; assert the detected `crop_region` matches the rectangle bounds within ±10px.

- [x] T006 [P] [US1] Add `_isolate_bold_lines(self, gray: NDArray) -> NDArray` to `ClassicalBorderDetector` in `src/cad_image_cropper/detectors/classical_detector.py` — morphological OPEN with 4×4 MORPH_RECT kernel (`BORDER_OPEN_KERNEL_SIZE`), then `THRESH_BINARY + THRESH_OTSU` on inverted result
- [x] T007 [P] [US1] Add `_is_qualifying_rectangle(self, approx: NDArray, x: int, y: int, w: int, h: int, img_w: int, img_h: int) -> bool` to `ClassicalBorderDetector` in `src/cad_image_cropper/detectors/classical_detector.py` — check: len(approx)==4, isContourConvex, w >= img_w * BORDER_MIN_WIDTH_RATIO, h >= img_h * BORDER_MIN_HEIGHT_RATIO
- [x] T008 [P] [US1] Add `_to_crop_region(self, x: int, y: int, w: int, h: int) -> CropRegion` to `ClassicalBorderDetector` in `src/cad_image_cropper/detectors/classical_detector.py` — return `CropRegion(x_start=x, x_end=x+w, y_start=y, y_end=y+h)`
- [x] T009 [US1] Add `_find_panel_contours(self, binary: NDArray, img_w: int, img_h: int) -> list[tuple[int, int, int, int]]` to `ClassicalBorderDetector` in `src/cad_image_cropper/detectors/classical_detector.py` — `findContours(RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)`, for each contour: `approxPolyDP(0.02 * arcLength)`, call `_is_qualifying_rectangle`; return list of `(x, y, w, h)` tuples; depends on T006, T007

**Checkpoint**: Detection helper methods complete — selection and orchestration can now be added

---

## Phase 4: User Story 2 — Select Widest Panel When Multiple Bordered Regions Exist (Priority: P1)

**Goal**: When multiple qualifying bordered panels are found, select the one with the greatest width; use smallest left-edge x as tiebreaker.

**Independent Test**: Process a synthetic PNG with two thick rectangles (wide + narrow); assert `crop_region` matches the wider rectangle.

- [x] T010 [US2] Add `_select_widest_panel(self, candidates: list[tuple[int, int, int, int]]) -> tuple[int, int, int, int] | None` to `ClassicalBorderDetector` in `src/cad_image_cropper/detectors/classical_detector.py` — sort by width descending then x ascending, return first element or None if empty; depends on T009
- [x] T011 [US2] Rewrite `ClassicalBorderDetector.detect_border(self, metadata: ImageMetadata, image_array: NDArray) -> DetectionResult` in `src/cad_image_cropper/detectors/classical_detector.py` — orchestration: `_convert_to_grayscale_array` → `_isolate_bold_lines` → `_find_panel_contours` → `_select_widest_panel` (→ `_no_detection()` if None) → `_to_crop_region` → `DetectionResult(crop_region=..., confidence=None, method=DetectionMethod.CLASSICAL)`; wrap cv2 calls in `try/except (cv2.error, ValueError, IndexError)` raising `BorderDetectionError`; remove all old HoughLinesP methods; depends on T009, T010

**Checkpoint**: ClassicalBorderDetector rewrite complete — US1 and US2 fully implemented and testable

---

## Phase 5: Polish & Quality Gates

**Purpose**: Update tests to reflect the new model and detection approach; ensure ruff, mypy, and pytest all pass.

- [x] T012 [P] Rewrite `ClassicalBorderDetector` tests in `tests/unit/test_detectors.py` — add 5 tests: `test_detects_bold_border_rectangle` (8px rectangle ≥40%w/≥50%h, assert crop_region ±10px), `test_rejects_thin_border` (1px rectangle → method==NONE), `test_rejects_small_panel` (thick border 30% width → method==NONE), `test_selects_widest_when_multiple` (wide+narrow → wider crop_region), `test_returns_none_for_blank_image` (white image → method==NONE); update `TwoStageDetector` tests to use `crop_region`
- [x] T013 [P] Update `tests/unit/test_models.py` — add 3 tests: `test_detection_result_with_crop_region` (valid crop_region + method=CLASSICAL), `test_detection_result_none_has_null_crop_region` (method=NONE → crop_region=None), `test_detection_result_crop_region_required_for_classical` (method=CLASSICAL + crop_region=None → raises ValueError); remove x_coordinate tests
- [x] T014 [P] Update `tests/unit/test_services.py` — update `TestImageProcessorCropRegion` assertions to use `detection.crop_region` instead of `detection.x_coordinate`
- [x] T015 Update `tests/integration/test_pipeline.py` — update assertions: `test_single_image_crop` (synthetic thick-border PNG; output width+height match crop_region), `test_sample_image_crops_title_block` (real sample; output width/height within 70–95% of input), `test_no_border_is_skipped` (blank PNG → SKIPPED_NO_BORDER)
- [x] T016 [P] Run `uv run ruff check src/ tests/` and fix any violations
- [x] T017 [P] Run `uv run mypy src/` and fix any type errors (must pass --strict with zero issues)
- [x] T018 Run `uv run pytest tests/` — all tests must pass with zero failures

---

## Dependencies

```
T001
 └─ T002
     ├─ T003 (parallel)
     ├─ T004 (parallel)
     └─ T005
         └─ T006 (parallel)  ─┐
            T007 (parallel)  ─┤─ T009
            T008 (parallel)  ─┘    └─ T010
                                        └─ T011
                                             └─ T012 (parallel)
                                                T013 (parallel)
                                                T014 (parallel)
                                                T015
                                                 └─ T016 (parallel)
                                                    T017 (parallel)
                                                     └─ T018
```

## Parallel Execution Examples

**After T002 completes**: Run T003 and T004 in parallel (different files).

**After T005 completes**: Run T006, T007, and T008 in parallel (add independent methods to the same class).

**After T011 completes**: Run T012, T013, and T014 in parallel (different test files); T015 depends on T012–T014 passing.

**After T015 completes**: Run T016 and T017 in parallel (lint and type check); T018 follows.

## Implementation Strategy

**MVP scope**: Complete Phases 1–4 (T001–T011) to deliver a working contour-based detector. Phases 1 and 2 unlock all story work. T006–T008 can be written together as a batch since they are short helper methods in the same class.

**Incremental delivery**:
1. T001–T002: Model migration (breaking change — compile check)
2. T003–T005: Downstream fixes (all callers updated — compile check)
3. T006–T011: ClassicalBorderDetector complete rewrite (single file)
4. T012–T018: Test coverage and quality gates (no output until all pass)
