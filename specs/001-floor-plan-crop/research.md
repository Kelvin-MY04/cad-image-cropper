# Research: CAD Floor Plan Panel Crop

**Branch**: `001-floor-plan-crop` | **Date**: 2026-03-04

---

## HuggingFace Model Selection

**Decision**: `facebook/sam-vit-base` (Segment Anything Model — ViT Base variant)

**Rationale**:
- Zero-shot, prompt-free operation: no labeled CAD dataset required.
- SAM segments arbitrary image regions; post-processing then identifies the separator mask by
  geometric properties (tall height, narrow width, near-vertical aspect ratio).
- Trained on 11M images and 1B masks — handles clean geometric line art robustly.
- 93.7M parameters, ~375 MB download, practical for a local tool.
- Two complementary usage strategies for this task:
  - Automatic mode: let SAM find all regions, filter for separator geometry.
  - Prompted mode (recommended): supply approximate x from classical pre-pass as a point
    prompt, giving SAM a strong prior and improving mask precision and inference speed.
- Native `transformers` support via `SamModel` and `SamProcessor` (transformers >= 4.29).
- `outputs.iou_scores` provides a confidence signal; scores below ~0.75 trigger fallback.

**Python 3.14 risk**: PyTorch (SAM's backend) does not publish stable wheels for Python 3.14
as of 2026-03. The SAM integration path requires Python 3.11 or 3.12 for PyTorch. The
classical fallback (Pillow + OpenCV + numpy) is fully Python-3.14 compatible. **Mitigation**:
pin `requires-python = ">=3.11"` in `pyproject.toml` (not 3.14) until PyTorch ships 3.14
wheels, or target 3.12 which is the current LTS.

**Integration Architecture (two-stage)**:
1. Classical pre-pass: compute column-wise darkness profile to produce a fast approximate
   x-candidate. Always runs; free and 3.14-compatible.
2. SAM prompted mode (primary): supply the classical candidate x as a point prompt. Use
   `iou_scores` as the confidence gate (threshold: 0.75).
3. If SAM confidence < 0.75 or model unavailable: OpenCV `HoughLinesP` with morphological
   vertical pre-processing as the sole classical fallback.
4. If both fail: skip the file and emit a warning.

**Alternatives rejected**:

| Model | Why rejected |
|-------|-------------|
| `IDEA-Research/grounding-dino-tiny` | 689 MB; text prompts fragile for thin structural lines; imprecise bboxes for 3-pixel lines |
| `facebook/detr-resnet-50` | COCO-trained, no separator class; needs full fine-tuning dataset |
| `microsoft/layoutlmv3-base` | Requires OCR text input; trained on text documents, not CAD drawings |

---

## Image Processing Library Stack

**Decision**: Pillow >= 11 for all PNG I/O; OpenCV headless for line detection only.

**Rationale**:
- Pillow is the only Python library with full `pHYs` chunk support: `img.info.get("dpi")`
  reads DPI as a `(float, float)` tuple; passing `dpi=...` to `save()` writes the chunk.
- `Image.crop()` does NOT copy `info` to the new image — DPI must be captured before
  cropping and passed explicitly to `save()`. This is a critical implementation constraint.
- OpenCV strips all metadata on `imread` — it MUST NOT be used for file I/O; only for
  producing a numpy array for HoughLinesP.
- imageio v3 wraps Pillow for PNG anyway, adding an unnecessary dependency.

**HoughLinesP pre-processing strategy**:
1. Convert to grayscale, invert (dark lines → bright).
2. Apply morphological vertical open (kernel: 1 × `max(50, height/20)`) to suppress all
   non-vertical structure before Hough.
3. Binary threshold.
4. `HoughLinesP(rho=1, theta=π/180, threshold=100, minLineLength=height*0.5, maxLineGap=20)`.
5. Filter to near-vertical lines (|x2−x1| ≤ 5 px).
6. Histogram cluster by x-coordinate (bin width 10 px), pick dominant bin.
7. Reject if result is within 5% of the image edge.

---

## CLI Framework

**Decision**: Typer

**Rationale**:
- Type annotation-native: `Optional[Path]` maps directly to `--output-dir` with zero
  boilerplate.
- Rich terminal output built-in: batch progress feedback and colored warnings.
- `typer.testing.CliRunner` for contract tests — no sys.argv mocking.
- Typer is pure Python — fully compatible with Python 3.14 (unlike torch).
- argparse rejected: verbose subcommand setup, no rich output, no annotation integration.
- Click rejected: slightly more boilerplate than Typer for this use case; no advantage given
  the project already mandates type annotations.

---

## Project Environment

**Decision**: uv with `.python-version` pinned to 3.12.x (not 3.14) pending PyTorch wheels.

**Rationale**:
- uv manages hermetic interpreter installs; `uv python pin 3.12` locks the interpreter.
- PyTorch has no stable Python 3.14 wheels as of March 2026. The transformers/SAM dependency
  chain (torch, torchvision) is the blocker.
- When PyTorch publishes 3.14 wheels, updating `.python-version` to `3.14.3` and
  `pyproject.toml` `requires-python = ">=3.14"` is the only change required.
- All non-torch dependencies (Pillow, OpenCV, Typer, numpy) are 3.14-compatible today.

**pyproject.toml key fields**:
```toml
[project]
requires-python = ">=3.12"
dependencies = [
    "pillow>=11.0.0",
    "opencv-python-headless>=4.10.0",
    "typer>=0.12.0",
    "numpy>=2.1.0",
    "transformers>=4.40.0",
    "torch>=2.4.0",
]

[project.scripts]
cad-crop = "cad_image_cropper.cli:app"

[tool.uv]
python = "3.12"
```

---

## Output Filename Collision Strategy

**Decision**: Append incrementing numeric suffix before extension.

`floor_plan.png` → check exists → `floor_plan_1.png` → check exists → `floor_plan_2.png`

This is encapsulated in a single `resolve_output_path(output_dir, stem, suffix)` method on
the `ImageExporter` class — the only authoritative implementation of this rule (DRY).

---

## Default Input/Output Directories

**Decision**: `/import` (input default) and `/export` (output default) per user specification.

The CLI `--input-dir` defaults to `/import` and `--output-dir` defaults to `/export`. These
are module-level constants `DEFAULT_INPUT_DIR` and `DEFAULT_OUTPUT_DIR` defined once in
`cad_image_cropper/constants.py`.
