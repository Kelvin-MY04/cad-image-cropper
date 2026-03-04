# Data Model: CAD Floor Plan Panel Crop

**Branch**: `001-floor-plan-crop` | **Date**: 2026-03-04

---

## Enumerations

### `DetectionMethod`

Represents which detection strategy located the border.

| Value | Meaning |
|-------|---------|
| `MODEL_SAM` | Border located by the SAM HuggingFace model |
| `CLASSICAL` | Border located by the OpenCV HoughLinesP classical fallback |
| `NONE` | No border located by either method |

### `ProcessingStatus`

Represents the outcome of processing a single image file.

| Value | Meaning |
|-------|---------|
| `SUCCESS` | Image cropped and exported successfully |
| `SKIPPED_NO_BORDER` | Neither detector found a border; file skipped with warning |
| `SKIPPED_CORRUPT` | File could not be opened as a valid PNG; file skipped with warning |
| `FAILED` | An unexpected error occurred during processing |

---

## Data Classes

### `ImageMetadata`

Holds read-only properties extracted from an input PNG file at load time.

| Field | Type | Constraints |
|-------|------|-------------|
| `file_path` | `Path` | Must exist; must have `.png` extension (case-insensitive) |
| `width` | `int` | > 0 |
| `height` | `int` | > 0 |
| `dpi` | `tuple[float, float] \| None` | X and Y DPI from pHYs chunk; None if chunk absent |
| `color_mode` | `str` | Pillow mode string: `"RGB"`, `"RGBA"`, `"L"`, etc. |

### `DetectionResult`

Holds the output of a single border detection attempt.

| Field | Type | Constraints |
|-------|------|-------------|
| `x_coordinate` | `int \| None` | Pixel x position of the separator left edge; None if not found |
| `confidence` | `float \| None` | Model confidence 0.0–1.0; None for classical detection |
| `method` | `DetectionMethod` | Which strategy produced this result |

**Rules**:
- If `method` is `NONE`, then `x_coordinate` must be `None`.
- If `method` is `MODEL_SAM`, then `confidence` must be present (0.0–1.0).
- If `method` is `CLASSICAL`, then `confidence` is `None` (no score from HoughLinesP).

### `CropRegion`

Defines the pixel bounding box to retain from the input image.

| Field | Type | Constraints |
|-------|------|-------------|
| `x_start` | `int` | Always 0 (left edge of image) |
| `x_end` | `int` | The separator x_coordinate; must be > 0 and < image width |
| `y_start` | `int` | Always 0 (top edge of image) |
| `y_end` | `int` | Full image height (unchanged) |

**Derived invariant**: `width = x_end - x_start`; `height = y_end - y_start` equals input height.

### `ProcessingResult`

Summarises the outcome of processing a single input image.

| Field | Type | Constraints |
|-------|------|-------------|
| `input_path` | `Path` | The source file path |
| `output_path` | `Path \| None` | The written output file path; None when status is not SUCCESS |
| `status` | `ProcessingStatus` | The processing outcome |
| `warning_message` | `str \| None` | Human-readable warning when status is not SUCCESS; None on SUCCESS |
| `detection_method` | `DetectionMethod` | Which method detected the border (NONE if skipped) |

---

## Exception Hierarchy

All exceptions inherit from `CadImageCropperError` (project base exception, inherits `Exception`).

```
CadImageCropperError
├── InvalidImageError         # File is not a valid PNG or cannot be opened
├── BorderDetectionError      # Both detection stages failed; no border found
├── ModelLoadError            # HuggingFace model download/load failed
└── ExportError               # Output file could not be written
```

Each exception carries a descriptive `message: str` and `file_path: Path` attribute to
satisfy the error handling contract (Principle VI).

---

## Class Responsibilities

### Core Interfaces (Abstract Base Classes)

| Class | Location | Single Responsibility |
|-------|----------|-----------------------|
| `BorderDetector` | `detectors/border_detector.py` | Abstract contract: accept `ImageMetadata` + numpy array, return `DetectionResult` |

### Concrete Detectors

| Class | Location | Single Responsibility |
|-------|----------|-----------------------|
| `SamBorderDetector` | `detectors/sam_detector.py` | Load SAM model; run prompted inference; return `DetectionResult` with `MODEL_SAM` method |
| `ClassicalBorderDetector` | `detectors/classical_detector.py` | Run HoughLinesP pipeline on numpy array; return `DetectionResult` with `CLASSICAL` method |
| `TwoStageDetector` | `detectors/two_stage_detector.py` | Orchestrate SAM → classical fallback; return first successful `DetectionResult` |

### Services

| Class | Location | Single Responsibility |
|-------|----------|-----------------------|
| `ImageLoader` | `services/image_loader.py` | Open PNG with Pillow; validate; return `(ImageMetadata, Image)` pair |
| `ImageCropper` | `services/image_cropper.py` | Accept `Image` + `CropRegion`; return cropped `Image` |
| `ImageExporter` | `services/image_exporter.py` | Accept cropped `Image` + `ImageMetadata` + output dir; resolve filename collision; write PNG with DPI preserved |
| `ImageProcessor` | `services/image_processor.py` | Orchestrate load → detect → crop → export for a single file; return `ProcessingResult` |
| `BatchProcessor` | `services/batch_processor.py` | Accept a directory path; iterate PNG files; delegate to `ImageProcessor`; collect and return `list[ProcessingResult]` |

### Entry Point

| Module | Location | Single Responsibility |
|--------|-----------|-----------------------|
| `cli` | `cli.py` | Parse CLI arguments with Typer; delegate to `ImageProcessor` or `BatchProcessor`; format and emit output |

---

## State Transitions: Single Image Processing

```
file_path
    │
    ▼
ImageLoader.load_image()
    │ success → (ImageMetadata, PIL.Image)
    │ failure → ProcessingResult(SKIPPED_CORRUPT)
    ▼
TwoStageDetector.detect_border()
    │ SAM high confidence  → DetectionResult(MODEL_SAM, x, confidence)
    │ SAM low confidence   → ClassicalBorderDetector.detect_border()
    │     classical found  → DetectionResult(CLASSICAL, x, None)
    │     classical none   → DetectionResult(NONE, None, None)
    │ model unavailable    → ClassicalBorderDetector.detect_border() (warn once)
    ▼
    DetectionResult.method == NONE?
    │ yes → ProcessingResult(SKIPPED_NO_BORDER)
    │ no  ▼
ImageCropper.crop_image()
    │ returns cropped PIL.Image
    ▼
ImageExporter.export_image()
    │ success → ProcessingResult(SUCCESS, output_path)
    │ failure → ProcessingResult(FAILED, warning_message)
```
