# CAD Image Cropper

A CLI tool that automatically detects and removes the detail/legend panel from CAD floor plan PNG images, keeping only the floor plan region with the original DPI metadata intact.

It uses a two-stage border detection strategy: a HuggingFace SAM model as the primary detector, falling back to OpenCV classical line detection when model confidence is low or the model is unavailable.

---

## How It Works

CAD floor plan exports typically contain a two-panel layout: the floor plan on the left and a detail/legend panel on the right, separated by a dark bold vertical border. This tool:

1. Loads the input PNG via Pillow (preserving DPI metadata)
2. Detects the vertical separator border using SAM (`facebook/sam-vit-base`) — falls back to OpenCV `HoughLinesP` if confidence is low or the model cannot be loaded
3. Crops the image to the left panel only
4. Exports the result as a PNG with the same DPI as the input

---

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- Python 3.12 (uv installs it automatically)
- ~400 MB free disk space for the SAM model cache (downloaded once on first run)
- Internet access on first run (to download `facebook/sam-vit-base` from HuggingFace)

---

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd cad-image-cropper

# Install all dependencies into a managed virtual environment
uv sync

# Verify the CLI is available
uv run cad-crop --help
```

---

## Usage

### Zero-argument batch processing (default workflow)

Place PNG files into `/import/` and run with no arguments:

```bash
uv run cad-crop
```

All `*.png` files in `/import/` are processed and results written to `/export/`. A summary line is printed at the end:

```
Processed: 12 | Skipped: 1 | Failed: 0
```

If `/import/` contains no PNG files:

```
No PNG files found in /import.
```

On first run the SAM model (~375 MB) is downloaded to `~/.cache/huggingface/hub/`. Subsequent runs load from cache instantly.

### Crop a single image

```bash
uv run cad-crop /import/floor_plan_A.png
```

Output is written to `/export/floor_plan_A.png`.

### Crop a single image to a custom output directory

```bash
uv run cad-crop /import/floor_plan_A.png --output-dir /my/results
```

The output directory is created automatically if it does not exist.

### Batch crop a specific directory

```bash
uv run cad-crop /some/other/dir
```

All `*.png` files in that directory are processed. Results appear in `/export/`. Files that cannot have their border detected emit a warning to stderr but do not stop the batch.

### Batch crop with a custom output directory

```bash
uv run cad-crop /import --output-dir /my/results
```

### Verbose output

```bash
uv run cad-crop --verbose
```

Prints one line per successfully processed file:

```
OK: floor_plan_A.png -> /export/floor_plan_A.png
OK: floor_plan_B.png -> /export/floor_plan_B.png
```

---

## CLI Reference

```
cad-crop [OPTIONS] [INPUT_PATH]
```

| Argument / Option | Short | Type | Default | Description |
|-------------------|-------|------|---------|-------------|
| `[INPUT_PATH]` | | Path | `/import` | Path to a single PNG file or a directory of PNG files |
| `--output-dir` | `-o` | Path | `/export` | Directory where cropped output files are written |
| `--verbose` | `-v` | flag | `False` | Print per-file success messages in addition to warnings |
| `--help` | | | | Show usage and exit |

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | All files processed (some may have been skipped with warnings) |
| `1` | Fatal error: INPUT_PATH does not exist |

---

## Output Filename Rules

- The output filename matches the input filename.
- If a file with the same name already exists in the output directory, a numeric suffix is inserted before the extension:
  - `floor_plan.png` → `floor_plan_1.png` → `floor_plan_2.png` → …

---

## Warnings and Errors

All warnings and errors are written to stderr.

| Situation | Message |
|-----------|---------|
| SAM model unavailable (once per run) | `WARNING: HuggingFace model could not be loaded — running in classical detection mode only.` |
| No border detected in a file | `WARNING: No border detected in <filename> — skipped.` |
| Corrupt or unreadable PNG | `WARNING: Could not open <filename> as a valid PNG — skipped.` |
| Unexpected per-file error | `ERROR: <filename> failed — <descriptive message>.` |

---

## Offline / No HuggingFace Access

If the SAM model cannot be downloaded or loaded, the tool automatically falls back to classical OpenCV line detection for the entire run and emits a one-time warning. Processing continues normally.

---

## Project Structure

```
src/cad_image_cropper/
├── cli.py              # Typer entry point
├── constants.py        # DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR, SAM_CONFIDENCE_THRESHOLD
├── exceptions.py       # CadImageCropperError hierarchy
├── models/             # Enums and dataclasses (ImageMetadata, DetectionResult, etc.)
├── detectors/          # BorderDetector ABC, SamBorderDetector, ClassicalBorderDetector, TwoStageDetector
└── services/           # ImageLoader, ImageCropper, ImageExporter, ImageProcessor, BatchProcessor

tests/
├── unit/
├── integration/
└── contract/
```

---

## Development

### Run tests

```bash
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/contract/

# Or all at once
uv run pytest tests/
```

### Lint and type-check

```bash
uv run ruff check src/ tests/
uv run mypy src/
```

Both must exit with zero errors before any commit.

### Dependencies

| Package | Version | Role |
|---------|---------|------|
| Pillow | >= 11 | All PNG file I/O and DPI metadata |
| opencv-python-headless | >= 4.10 | Classical border detection (HoughLinesP) |
| transformers | >= 4.40 | HuggingFace model inference |
| torch | >= 2.4 | PyTorch backend for SAM |
| numpy | >= 2.1 | Numeric array operations |
| typer | >= 0.12 | CLI framework |

---

## Assumptions and Limitations

- Input files must be PNG format; other formats are not supported.
- Images must follow a two-panel horizontal layout: floor plan on the left, detail/legend panel on the right.
- The separator border must be a vertical dark bold line — horizontal separators are not detected.
- The tool never modifies, renames, or deletes input files.
- Skipped files (no border detected) count as warnings, not failures, and do not affect the exit code.
