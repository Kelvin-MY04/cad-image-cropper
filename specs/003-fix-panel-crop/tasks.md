# Tasks: Fix Panel Detection and Cropping

**Input**: Design documents from `/specs/003-fix-panel-crop/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files or no incomplete dependencies)
- **[Story]**: User story this task belongs to (US1/US2/US3)

---

## Phase 1: Setup

**Purpose**: Add new constants that gate all algorithm changes.

- [x] T001 Add `SEPARATOR_MIN_HEIGHT_RATIO`, `TITLE_BLOCK_ZONE_LEFT_RATIO`, `TITLE_BLOCK_ZONE_RIGHT_RATIO` constants to `src/cad_image_cropper/constants.py`

**Checkpoint**: Constants available for import — algorithm changes can begin.

---

## Phase 2: Foundational (Blocking Prerequisite)

**Purpose**: Change `_filter_vertical_lines` return type — this method is called by `detect_border` and determines all downstream processing; must be settled before any new helper methods are added.

**⚠️ CRITICAL**: T002 must be complete before Phase 3 begins.

- [x] T002 Modify `_filter_vertical_lines` in `src/cad_image_cropper/detectors/classical_detector.py` to return `list[tuple[int, int, int]]` where each tuple is `(x_mid, y_top, y_bottom)` instead of `list[int]`

**Checkpoint**: Foundation ready — new helper methods can now be added.

---

## Phase 3: User Story 1+2 — Core Detection Algorithm (Priority: P1) 🎯 MVP

**Goal**: Replace the "most common x" selection with a height-aware right-zone search so the detector correctly targets the title block separator, not interior floor plan lines.

**Independent Test**: Run `uv run pytest tests/unit/test_detectors.py -k "test_detects_vertical_stripe"` after T006; the detected x should be within 20px of `stripe_x=900`.

### Implementation

- [x] T003 [P] [US1] Add `_aggregate_x_bins(segments: list[tuple[int, int, int]]) -> dict[int, list[tuple[int, int]]]` method to `ClassicalBorderDetector` in `src/cad_image_cropper/detectors/classical_detector.py` — groups y-spans by x-bin key (`x_mid // 10`)
- [x] T004 [P] [US1] Add `_compute_y_coverage(spans: list[tuple[int, int]], image_height: int) -> float` method to `ClassicalBorderDetector` in `src/cad_image_cropper/detectors/classical_detector.py` — merges overlapping y-intervals and returns coverage ratio
- [x] T005 [US1] Add `_select_separator_x(bins: dict[int, list[tuple[int, int]]], image_width: int, image_height: int) -> int | None` method to `ClassicalBorderDetector` in `src/cad_image_cropper/detectors/classical_detector.py` — filters bins to right zone + height threshold, returns leftmost qualifying x (depends on T003, T004)
- [x] T006 [US1] Remove `_cluster_and_select_dominant_x` and update `detect_border` call chain in `src/cad_image_cropper/detectors/classical_detector.py` to: `segments = _filter_vertical_lines` → `bins = _aggregate_x_bins` → `x = _select_separator_x` (depends on T005)

**Checkpoint**: Core algorithm complete — detector now targets right-zone full-height separator.

---

## Phase 4: User Story 2 — Detection Target Tests (Priority: P1)

**Goal**: Verify the detector accepts only full-height lines in the right zone and rejects interior drawing lines.

**Independent Test**: `uv run pytest tests/unit/test_detectors.py` — all three detector tests pass.

- [x] T007 [P] [US2] Update `test_detects_vertical_stripe` in `tests/unit/test_detectors.py` — change `stripe_x=600` to `stripe_x=900` and expected tolerance to `abs(result.x_coordinate - 900) <= 20`
- [x] T008 [P] [US2] Add `test_rejects_stripe_in_drawing_zone` to `tests/unit/test_detectors.py` — synthetic image with `stripe_x=300` (25% of 1200px); assert `result.method == DetectionMethod.NONE`
- [x] T009 [P] [US2] Add `test_selects_leftmost_in_right_zone` to `tests/unit/test_detectors.py` — image with two stripes at `x=840` and `x=960`; assert detected x is within 20px of 840

**Checkpoint**: Unit tests confirm the new selection strategy is correct.

---

## Phase 5: User Story 1 — End-to-End Accuracy Tests (Priority: P1)

**Goal**: Verify the full pipeline produces a correctly cropped output matching the sample.

**Independent Test**: `uv run pytest tests/integration/test_pipeline.py` — both pipeline tests pass including the sample image regression test.

- [x] T010 [US1] Update `test_single_image_crop` in `tests/integration/test_pipeline.py` — change `stripe_x=600` to `stripe_x=900` and assertion from `out_img.width <= 620` to `out_img.width <= 950`
- [x] T011 [US1] Add `test_sample_image_crops_title_block` to `tests/integration/test_pipeline.py` — process `test/sample/input.png` through pipeline; assert output width is 70-95% of input width (ratio-based, robust to multi-scan mismatches); use `pytest.skip` if sample file absent

**Checkpoint**: Full pipeline validated against real CAD sample. US1 acceptance criterion SC-001 met.

---

## Phase 6: User Story 3 — Margin Preservation Verification (Priority: P2)

**Goal**: Confirm that the crop box formula `(0, 0, separator_x, image_height)` in `ImageProcessor._build_crop_region` is unmodified and correct — no additional inset trimming applied.

**Independent Test**: Inspect `src/cad_image_cropper/services/image_processor.py:_build_crop_region` — x_start=0, x_end=detection.x_coordinate, y_start=0, y_end=metadata.height.

- [x] T012 [US3] Verify `_build_crop_region` in `src/cad_image_cropper/services/image_processor.py` produces `CropRegion(x_start=0, x_end=x_coordinate, y_start=0, y_end=height)` with no additional inset; add assertion in `tests/unit/test_services.py` confirming crop region dimensions

**Checkpoint**: FR-003 confirmed — crop boundary is exactly the separator line.

---

## Phase 7: Polish & Quality Gates

**Purpose**: Ensure zero lint and type errors; full test suite green.

- [x] T013 [P] Run `uv run ruff check src/ tests/` and fix all violations
- [x] T014 [P] Run `uv run mypy src/` and fix all type errors (strict mode)
- [x] T015 Run `uv run pytest tests/` and confirm all tests pass with no regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1
- **Phase 3 (Core Algorithm)**: Depends on Phase 2 — T003 and T004 can run in parallel; T005 depends on T003+T004; T006 depends on T005
- **Phase 4 (Unit Tests)**: Depends on Phase 3 — T007, T008, T009 all parallelizable
- **Phase 5 (Integration Tests)**: Depends on Phase 3 — T010 and T011 sequential
- **Phase 6 (Margin Verification)**: Depends on Phase 3
- **Phase 7 (Polish)**: Depends on all prior phases

### Parallel Opportunities

```bash
# Phase 3: after T002, launch T003 and T004 in parallel
Task: "Add _aggregate_x_bins method"
Task: "Add _compute_y_coverage method"

# Phase 4: after Phase 3, launch T007, T008, T009 in parallel
Task: "Update test_detects_vertical_stripe"
Task: "Add test_rejects_stripe_in_drawing_zone"
Task: "Add test_selects_leftmost_in_right_zone"

# Phase 7: launch T013 and T014 in parallel
Task: "Run ruff check"
Task: "Run mypy --strict"
```

---

## Implementation Strategy

### MVP (US1+US2, Phases 1–5)

1. Complete Phase 1: Add constants
2. Complete Phase 2: Refactor `_filter_vertical_lines`
3. Complete Phase 3: Implement new detection algorithm
4. Complete Phase 4+5: Update and add tests
5. **STOP and VALIDATE**: `uv run pytest tests/` — all green
6. Process `test/sample/input.png` — verify title block removed

### Full Delivery (Phases 1–7)

- Add US3 margin verification (Phase 6)
- Run all quality gates (Phase 7)

---

## Notes

- T001 is a prerequisite for all algorithm tasks — must be committed first
- T002 is the riskiest change — the method signature change cascades through `detect_border`
- After T006, run the existing tests manually to confirm no regressions before adding new tests
- `test/sample/` files are untracked — ensure they exist before running T011
- Total tasks: 15 | Parallelizable: 7 | Linear issues: 5
