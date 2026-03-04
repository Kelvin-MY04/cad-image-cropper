# Quickstart: Modify Data Flow

**Branch**: `002-modify-data-flow` | **Date**: 2026-03-04

---

## Prerequisites

- [uv](https://docs.astral.sh/uv/) installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Python 3.12 (uv installs it automatically)
- ~400 MB free disk space for the SAM model cache (one-time download)

---

## Setup

```bash
cd /path/to/cad-image-cropper
uv sync
uv run cad-crop --help
```

---

## Zero-Argument Batch Processing (New Default Workflow)

Place PNG files into `/import/`, then run with no arguments:

```bash
uv run cad-crop
```

The tool reads all `*.png` files from `/import/` and writes cropped results to `/export/`.
Both directories are used automatically — no path arguments needed.

A summary is printed at the end:

```
Processed: 12 | Skipped: 1 | Failed: 0
```

If `/import/` contains no PNG files:

```
No PNG files found in /import.
```

---

## Crop a Single Image

```bash
uv run cad-crop /import/floor_plan_A.png
```

The cropped file is written to `/export/floor_plan_A.png`.

---

## Batch Crop a Specific Directory

```bash
uv run cad-crop /some/other/dir
```

All `*.png` files in that directory are processed; results go to `/export/`.

---

## Custom Output Directory

```bash
uv run cad-crop --output-dir /my/results
# or with explicit input:
uv run cad-crop /import --output-dir /my/results
```

The output directory is created automatically if it does not exist.

---

## Verbose Output

```bash
uv run cad-crop --verbose
```

Prints one `OK: filename -> output_path` line per successfully processed file.

---

## Offline / No HuggingFace Access

If the SAM model cannot be downloaded, the tool falls back to classical line detection:

```
WARNING: HuggingFace model could not be loaded — running in classical detection mode only.
```

Processing continues normally using OpenCV-based detection.

---

## Handling Filename Collisions

If `/export/floor_plan_A.png` already exists, the new output is saved as
`/export/floor_plan_A_1.png`. Subsequent collisions produce `_2.png`, `_3.png`, etc.
Existing files are never overwritten.

---

## Error Scenarios

| Situation | Message | Exit Code |
|-----------|---------|-----------|
| `/import` does not exist | `ERROR: /import does not exist.` | 1 |
| `/import` has no PNG files | `No PNG files found in /import.` | 0 |
| A single file is corrupt | `WARNING: Could not open … — skipped.` | 0 |
| Output write fails | `ERROR: … failed — <reason>.` | 0 |

---

## Running Tests

```bash
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/contract/
```

---

## Code Quality Checks

```bash
uv run ruff check src/ tests/
uv run mypy src/
```

Both must exit with zero errors before any commit.

---

## Validation Checklist

- [ ] `uv run cad-crop --help` shows `[INPUT_PATH]` as optional (bracketed)
- [ ] `uv run cad-crop` (no args) processes all PNG files in `/import/` into `/export/`
- [ ] `uv run cad-crop` on empty `/import/` prints "No PNG files found" and exits 0
- [ ] `uv run cad-crop /nonexistent` exits with code 1 and error message
- [ ] Explicit path still works: `uv run cad-crop /import/file.png`
- [ ] `--output-dir` override writes to the specified directory
- [ ] Duplicate output filename produces `_1.png` suffix
- [ ] `ruff check` and `mypy` both pass with zero violations
