# Data Model: Image Detection and Cropping — Left Panel Border Crop

**Feature**: 004-crop-left-panel
**Branch**: `004-crop-left-panel`
**Date**: 2026-03-05

## Overview

This feature replaces the `x_coordinate`-based `DetectionResult` with a `crop_region`-based model, enabling the detector to return a full 4-sided bounding box instead of a single vertical separator coordinate. No new domain entities are introduced; two existing models are modified.

---

## Modified Entities

### `DetectionResult` (modified)

**File**: `src/cad_image_cropper/models/detection_result.py`

| Field | Type | Before | After | Notes |
|---|---|---|---|---|
| `x_coordinate` | `int \| None` | present | **removed** | Replaced by `crop_region` |
| `crop_region` | `CropRegion \| None` | absent | **added** | The full bounding box of the detected panel |
| `confidence` | `float \| None` | unchanged | unchanged | Still required when method is MODEL_SAM |
| `method` | `DetectionMethod` | unchanged | unchanged | |

**Validation rules (updated)**:
- `crop_region` MUST be `None` when `method == DetectionMethod.NONE`
- `crop_region` MUST be non-`None` when `method != DetectionMethod.NONE`
- `confidence` MUST be non-`None` when `method == DetectionMethod.MODEL_SAM`

---

### `CropRegion` (unchanged)

**File**: `src/cad_image_cropper/models/crop_region.py`

No changes. Used as the type of `DetectionResult.crop_region`.

| Field | Type | Constraint |
|---|---|---|
| `x_start` | `int` | 0 ≤ x_start < x_end |
| `x_end` | `int` | x_end > x_start |
| `y_start` | `int` | 0 ≤ y_start < y_end |
| `y_end` | `int` | y_end > y_start |

---

## New Constants

**File**: `src/cad_image_cropper/constants.py`

| Constant | Type | Value | Purpose |
|---|---|---|---|
| `BORDER_OPEN_KERNEL_SIZE` | `int` | `3` | Morphological opening kernel; removes thin lines (1–2 px) while preserving bold borders (≥5 px) |
| `BORDER_MIN_HEIGHT_RATIO` | `float` | `0.50` | Panel bounding box height must span ≥ 50% of image height |
| `BORDER_MIN_WIDTH_RATIO` | `float` | `0.40` | Panel bounding box width must span ≥ 40% of image width |
| `BORDER_APPROX_POLY_EPSILON` | `float` | `0.02` | Fraction of contour perimeter used as epsilon in `approxPolyDP`; 2% gives robust rectangle approximation |
| `BORDER_MAX_VERTEX_COUNT` | `int` | `8` | Maximum vertex count for an "approximately rectangular" polygon; tolerates slight corner rounding |

---

## Affected Services / Detectors

| Class | Change |
|---|---|
| `ClassicalBorderDetector` | Complete rewrite: contour-based bold-border detection instead of HoughLinesP separator |
| `SamBorderDetector` | `_extract_x_from_mask` replaced by `_extract_crop_region_from_mask` returning `CropRegion` |
| `TwoStageDetector` | `_is_result_sufficient`: `result.x_coordinate is not None` → `result.crop_region is not None` |
| `ImageProcessor` | `_build_crop_region`: returns `detection.crop_region` directly instead of constructing from `x_coordinate` |

---

## State Transitions

```
ImageProcessor.process_image(file_path)
  │
  ├─ load_image → InvalidImageError → ProcessingResult(SKIPPED_CORRUPT)
  │
  ├─ detect_border → DetectionResult(method=NONE, crop_region=None)
  │     → ProcessingResult(SKIPPED_NO_BORDER)
  │
  └─ detect_border → DetectionResult(method=CLASSICAL, crop_region=CropRegion(x0,x1,y0,y1))
        → crop_image(CropRegion) → export_image → ProcessingResult(SUCCESS)
```
