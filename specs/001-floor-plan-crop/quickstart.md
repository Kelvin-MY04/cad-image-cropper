# Quickstart: CAD Floor Plan Panel Crop

**Branch**: `001-floor-plan-crop` | **Date**: 2026-03-04

---

## Prerequisites

- [uv](https://docs.astral.sh/uv/) installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Python 3.12 (uv installs it automatically)
- ~400 MB free disk space for the SAM model cache (one-time download)

---

## Setup

```bash
# Clone and enter the project
cd /path/to/cad-image-cropper

# Install dependencies and create virtual environment
uv sync

# Verify the CLI is available
uv run cad-crop --help
```

---

## Crop a Single Image

Place your floor plan PNG in `/import/`, then:

```bash
uv run cad-crop /import/floor_plan_A.png
```

The cropped file is written to `/export/floor_plan_A.png`.

On first run, the SAM model (~375 MB) is downloaded to `~/.cache/huggingface/hub/`.
Subsequent runs load from cache (fast).

---

## Batch Crop a Directory

```bash
uv run cad-crop /import
```

All `*.png` files in `/import/` are processed. Results appear in `/export/`.
A summary line is printed at the end:

```
Processed: 12 | Skipped: 1 | Failed: 0
```

Files that skip (no border detected) emit a warning to stderr but do not stop the batch.

---

## Custom Output Directory

```bash
uv run cad-crop /import --output-dir /my/results
```

The output directory is created automatically if it does not exist.

---

## Verbose Output

```bash
uv run cad-crop /import --verbose
```

Prints one `OK: filename -> output_path` line per successfully processed file.

---

## Offline / No HuggingFace Access

If the SAM model cannot be downloaded, the tool falls back to classical line detection only
and emits a one-time warning:

```
WARNING: HuggingFace model could not be loaded — running in classical detection mode only.
```

Processing continues normally using OpenCV-based detection.

---

## Handling Filename Collisions

If `/export/floor_plan_A.png` already exists from a previous run, the new output is saved as
`/export/floor_plan_A_1.png`. Subsequent collisions produce `_2.png`, `_3.png`, etc.

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

Use this list to verify a successful end-to-end run:

- [ ] `uv run cad-crop --help` prints usage without error
- [ ] Single image run produces output in `/export/` with same DPI as input
- [ ] Batch run on `/import/` produces one output per valid PNG
- [ ] An image with no border emits `WARNING: No border detected` and is skipped
- [ ] Running with `--output-dir` writes to the specified directory
- [ ] Duplicate output filename produces `_1.png` suffix
- [ ] `ruff check` and `mypy` both pass with zero violations
