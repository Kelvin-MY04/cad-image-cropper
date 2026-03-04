# Data Model: Modify Data Flow

**Branch**: `002-modify-data-flow` | **Date**: 2026-03-04

---

## Changes from Feature 001

This feature introduces **no new entities, enumerations, or exceptions**.

The existing data model (defined in `specs/001-floor-plan-crop/data-model.md`) is fully sufficient. The complete class hierarchy, `ProcessingResult`, `ProcessingStatus`, `ImageMetadata`, `CropRegion`, `DetectionResult`, and all exception types remain unchanged.

---

## Confirmed Invariants Supporting This Feature

The following existing behaviours satisfy the new requirements without modification:

### `ImageExporter._resolve_output_path()` — Collision Suffix

Satisfies **FR-010** (rename with numeric suffix on collision).

```
Input stem: "floor_plan"
/export/floor_plan.png exists   → try floor_plan_1.png
/export/floor_plan_1.png exists → try floor_plan_2.png
/export/floor_plan_2.png free   → write floor_plan_2.png
```

Counter is unbounded; no maximum suffix is imposed.

### `ImageExporter.export_image()` — Auto-Create Output Directory

Satisfies **FR-003** (create output dir if absent): `output_dir.mkdir(parents=True, exist_ok=True)` runs before every write. Raises `ExportError` if the directory cannot be created (permissions, etc.).

### `BatchProcessor._collect_png_files()` — Non-PNG Filtering

Satisfies **FR-008** (silent ignore of non-PNG files): only files with `suffix.lower() == ".png"` and `is_file() == True` are collected. Subdirectories are excluded implicitly by the `is_file()` guard.

### `ImageProcessor.process_image()` — Output Write Failure Continuation

Satisfies **FR-011** (skip + warn + continue on write failure): the `except CadImageCropperError` block in `process_image` catches `ExportError` and returns `ProcessingResult(FAILED, warning_message=str(exc))`. `BatchProcessor.process_directory` collects all results via list comprehension — it does not short-circuit on FAILED results.

---

## CLI Argument Model (Updated)

The only data-flow change is in the CLI argument signature. After this feature:

| Argument / Option | Mode | Type | Default | Resolved From |
|-------------------|------|------|---------|---------------|
| `INPUT_PATH` | Optional positional | `Path \| None` | `None` | Resolved to `DEFAULT_INPUT_DIR` (`/import`) when `None` |
| `--output-dir / -o` | Optional option | `Path \| None` | `DEFAULT_OUTPUT_DIR` | Resolved to `/export` when `None` |
| `--verbose / -v` | Optional flag | `bool` | `False` | — |

### Resolution Rules

1. If `INPUT_PATH` is `None` → use `DEFAULT_INPUT_DIR` (`/import`).
2. If resolved input path does not exist → error, exit 1.
3. If resolved input path is a directory → batch mode.
4. If resolved input path is a directory with zero PNG files → informative message, exit 0.
5. If resolved input path is a file → single-file mode.

---

## Exception Hierarchy (Unchanged)

```
CadImageCropperError
├── InvalidImageError         # File is not a valid PNG or cannot be opened
├── BorderDetectionError      # Both detection stages failed; no border found
├── ModelLoadError            # HuggingFace model download/load failed
└── ExportError               # Output file could not be written
```

No new exception types are introduced by this feature.
