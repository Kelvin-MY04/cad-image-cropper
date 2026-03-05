# Data Model: Fix Panel Detection and Cropping

**Branch**: `003-fix-panel-crop` | **Date**: 2026-03-05

## Summary

No new data model entities are introduced. All existing models (`DetectionResult`, `CropRegion`, `ImageMetadata`) remain unchanged. This feature modifies only the internal algorithm of `ClassicalBorderDetector`.

## Existing Models (unchanged)

### DetectionResult
| Field | Type | Constraint |
|---|---|---|
| `x_coordinate` | `int \| None` | Must be `None` when `method == NONE` |
| `confidence` | `float \| None` | Must be set when `method == MODEL_SAM` |
| `method` | `DetectionMethod` | Enum: `CLASSICAL`, `MODEL_SAM`, `NONE` |

### CropRegion
| Field | Type | Constraint |
|---|---|---|
| `x_start` | `int` | Must be < `x_end` |
| `x_end` | `int` | Must be > `x_start` |
| `y_start` | `int` | Must be < `y_end` |
| `y_end` | `int` | Must be > `y_start` |

### ImageMetadata
| Field | Type | Constraint |
|---|---|---|
| `file_path` | `Path` | Must exist |
| `width` | `int` | Positive |
| `height` | `int` | Positive |
| `dpi` | `tuple[float, float] \| None` | Preserved from source PNG |
| `color_mode` | `str` | e.g. `"RGB"`, `"L"` |

## Internal Type: VerticalSegment

An intermediate tuple used within `ClassicalBorderDetector` only — not a public model.

| Position | Type | Meaning |
|---|---|---|
| 0 | `int` | x-midpoint of the detected line segment |
| 1 | `int` | y-top (min y coordinate of segment) |
| 2 | `int` | y-bottom (max y coordinate of segment) |

**Type alias** (Python): `tuple[int, int, int]`
**Usage**: Return type of `_filter_vertical_lines`, consumed immediately by `_aggregate_x_bins`.

## New Constants (constants.py additions)

| Name | Type | Value | Purpose |
|---|---|---|---|
| `SEPARATOR_MIN_HEIGHT_RATIO` | `float` | `0.70` | Minimum fraction of image height a line cluster must span to qualify as a separator |
| `TITLE_BLOCK_ZONE_LEFT_RATIO` | `float` | `0.70` | Left boundary of title block search zone as fraction of image width |
| `TITLE_BLOCK_ZONE_RIGHT_RATIO` | `float` | `0.95` | Right boundary of title block search zone as fraction of image width |
