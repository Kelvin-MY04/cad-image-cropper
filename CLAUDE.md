# cad-image-cropper Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-04

## Active Technologies
- Python 3.12 + Typer >= 0.12 (CLI), Pillow >= 11 (PNG I/O), existing services (002-modify-data-flow)
- Filesystem only — `/import` (read), `/export` (write) (002-modify-data-flow)
- Python 3.12 + opencv-python-headless >= 4.10 (HoughLinesP), Pillow >= 11 (PNG I/O), numpy >= 2.1, typer >= 0.12 (003-fix-panel-crop)
- Filesystem only — PNG files read from `/import`, written to `/export` (003-fix-panel-crop)
- Python 3.12 + opencv-python-headless ≥ 4.10, numpy ≥ 2.1, Pillow ≥ 11, Typer ≥ 0.12 (004-crop-left-panel)

- **Language**: Python 3.12 (upgrade to 3.14.3 once PyTorch ships 3.14 wheels)
- **Package manager**: uv (`uv sync`, `uv run`)
- **Image I/O**: Pillow >= 11 (all PNG read/write; owns DPI metadata)
- **Line detection**: opencv-python-headless >= 4.10 (HoughLinesP only — never file I/O)
- **AI model**: transformers >= 4.40 + torch >= 2.4 (`facebook/sam-vit-base`)
- **CLI**: Typer >= 0.12
- **Numeric**: numpy >= 2.1

## Project Structure

```text
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

## Commands

```bash
uv sync                          # Install dependencies
uv run cad-crop --help           # Run CLI
uv run pytest tests/             # Run all tests
uv run ruff check src/ tests/    # Lint
uv run mypy src/                 # Type check (must pass --strict)
```

## Code Style

- Constitution v1.0.0 enforced: OOP, SOLID, DRY, clean code, SRP per method, error handling
- Python naming: `snake_case` for methods/variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants
- No comments anywhere in source code
- Type annotations required on all method signatures
- All I/O wrapped in try/except; custom exceptions from `CadImageCropperError`
- `ruff check` and `mypy --strict` must pass with zero errors before any commit

## Key Rules

- Pillow owns ALL PNG file I/O — OpenCV MUST NOT read or write files (strips DPI)
- `Image.crop()` does not copy `info` — capture `img.info.get("dpi")` before cropping
- Default input directory: `/import` | Default output directory: `/export`
- SAM model cache: `~/.cache/huggingface/hub/` (auto-downloaded on first run)

## Recent Changes
- 004-crop-left-panel: Added Python 3.12 + opencv-python-headless ≥ 4.10, numpy ≥ 2.1, Pillow ≥ 11, Typer ≥ 0.12
- 003-fix-panel-crop: Added Python 3.12 + opencv-python-headless >= 4.10 (HoughLinesP), Pillow >= 11 (PNG I/O), numpy >= 2.1, typer >= 0.12
- 002-modify-data-flow: Added Python 3.12 + Typer >= 0.12 (CLI), Pillow >= 11 (PNG I/O), existing services


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
