# Implementation Plan: CAD Floor Plan Panel Crop

**Branch**: `001-floor-plan-crop` | **Date**: 2026-03-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-floor-plan-crop/spec.md`

## Summary

Detect the dark bold vertical separator line in CAD floor plan PNG images using a two-stage
strategy (SAM HuggingFace model → OpenCV classical fallback), crop the left panel region,
and export the result as a PNG preserving the original DPI metadata exactly. Supports single
file and batch directory modes via a Typer CLI. Defaults: input from `/import`, output to
`/export`.

## Technical Context

**Language/Version**: Python 3.12 (PyTorch has no stable 3.14 wheels; upgrade to 3.14.3 when
PyTorch publishes them — the sole required change is `.python-version` and `requires-python`)
**Primary Dependencies**: Pillow >= 11, opencv-python-headless >= 4.10, transformers >= 4.40,
torch >= 2.4, numpy >= 2.1, typer >= 0.12
**Storage**: Local filesystem only — `/import` (input), `/export` (output), HuggingFace cache
(`~/.cache/huggingface/hub/`)
**Testing**: pytest with typer.testing.CliRunner for contract tests
**Target Platform**: Linux desktop (primary), macOS compatible
**Project Type**: CLI application
**Performance Goals**: Batch of 50 images within 5 minutes on standard desktop hardware
(SC-004)
**Constraints**: DPI metadata round-trip must be lossless (SC-002, SC-003); OpenCV MUST NOT
be used for file I/O (strips DPI); Pillow owns all PNG read/write
**Scale/Scope**: Single user, local files, up to ~50–100 images per batch

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. OOP | All production code in classes; no top-level functions outside CLI entry point | ✅ Pass — all domain logic in classes; CLI delegates to service classes |
| II. SOLID — SRP | `BorderDetector` ABC, `SamBorderDetector`, `ClassicalBorderDetector`, `TwoStageDetector`, `ImageLoader`, `ImageCropper`, `ImageExporter`, `ImageProcessor`, `BatchProcessor` — each has one reason to change | ✅ Pass |
| II. SOLID — OCP | New detector strategies extend `BorderDetector` ABC without modifying `TwoStageDetector` | ✅ Pass |
| II. SOLID — DIP | `TwoStageDetector` depends on `BorderDetector` ABC; concrete detectors injected at construction | ✅ Pass |
| II. SOLID — ISP | `BorderDetector` ABC exposes only `detect_border(metadata, array) -> DetectionResult` | ✅ Pass |
| III. DRY | Output filename collision logic in single `ImageExporter._resolve_output_path()` method; input/output defaults as module-level constants in `constants.py` | ✅ Pass |
| IV. Clean Code | `snake_case` throughout; no comments; named constants for magic values (`SAM_CONFIDENCE_THRESHOLD`, `DEFAULT_INPUT_DIR`, `DEFAULT_OUTPUT_DIR`); no inline literals | ✅ Pass |
| V. SRP per Method | Each method ≤ 20 lines; action-verb + object-noun naming enforced | ✅ Pass |
| VI. Error Handling | All I/O in try/except; custom exception hierarchy from `CadImageCropperError`; no silent suppression; descriptive messages with file path context | ✅ Pass |
| Code Quality | flake8 + mypy --strict gate on every commit; type annotations on all signatures | ✅ Pass |

**Post-Phase 1 re-check**: All gates remain valid after data model and contracts design.
No violations requiring Complexity Tracking entries.

## Project Structure

### Documentation (this feature)

```text
specs/001-floor-plan-crop/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── cli-contract.md  # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
└── cad_image_cropper/
    ├── __init__.py
    ├── cli.py                       # Typer entry point; delegates to services
    ├── constants.py                 # DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR, SAM_CONFIDENCE_THRESHOLD
    ├── exceptions.py                # CadImageCropperError hierarchy
    ├── models/
    │   ├── __init__.py
    │   ├── detection_method.py      # DetectionMethod enum
    │   ├── processing_status.py     # ProcessingStatus enum
    │   ├── image_metadata.py        # ImageMetadata dataclass
    │   ├── detection_result.py      # DetectionResult dataclass
    │   ├── crop_region.py           # CropRegion dataclass
    │   └── processing_result.py     # ProcessingResult dataclass
    ├── detectors/
    │   ├── __init__.py
    │   ├── border_detector.py       # BorderDetector ABC
    │   ├── sam_detector.py          # SamBorderDetector
    │   ├── classical_detector.py    # ClassicalBorderDetector
    │   └── two_stage_detector.py    # TwoStageDetector (composition)
    └── services/
        ├── __init__.py
        ├── image_loader.py          # ImageLoader
        ├── image_cropper.py         # ImageCropper
        ├── image_exporter.py        # ImageExporter (with collision handling)
        ├── image_processor.py       # ImageProcessor (single file orchestrator)
        └── batch_processor.py       # BatchProcessor (directory orchestrator)

tests/
├── unit/
│   ├── test_models.py
│   ├── test_detectors.py
│   └── test_services.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_cli_contract.py

pyproject.toml
.python-version                      # contains "3.12"
```

**Structure Decision**: Single project layout (Option 1). No frontend, no API server, no
mobile component. Source under `src/cad_image_cropper/` for clean packaging; tests under
`tests/` with three subdirectories matching the three test categories required by the
constitution.

## Complexity Tracking

> No constitution violations found — this table is empty by design.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| — | — | — |
