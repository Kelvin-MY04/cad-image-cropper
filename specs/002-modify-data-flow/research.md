# Research: Modify Data Flow

**Branch**: `002-modify-data-flow` | **Date**: 2026-03-04

---

## Findings

### Decision 1: Scope of Changes

**Decision**: Only `cli.py` requires modification. All other requirements are already satisfied by the existing implementation.

**Rationale**: A review of the existing codebase reveals:

| Requirement | Already Satisfied By |
|-------------|----------------------|
| FR-002: default `/export` output | `DEFAULT_OUTPUT_DIR` constant + CLI default |
| FR-003: create output dir if absent | `ImageExporter.export_image()` → `mkdir(parents=True, exist_ok=True)` |
| FR-008: ignore non-PNG files | `BatchProcessor._collect_png_files()` filters `suffix.lower() == ".png"` |
| FR-010: suffix rename on collision | `ImageExporter._resolve_output_path()` → `_1`, `_2`, … loop |
| FR-011: continue batch on write fail | `ImageProcessor.process_image()` catches `CadImageCropperError` → `ProcessingResult(FAILED)`; `_run_batch` loops continue |

Only two gaps exist relative to the spec:

1. `input_path` in `cli.py` is a mandatory `typer.Argument(...)` — FR-001 requires it to default to `DEFAULT_INPUT_DIR`.
2. When no PNG files are found in the input directory, the existing output (`Processed: 0 | Skipped: 0 | Failed: 0`) is technically correct but does not meet SC-005's "informative, human-readable" standard.

**Alternatives considered**: Adding an `--input-dir` option (as sketched in the 001 contract) was rejected in favour of making `INPUT_PATH` an optional positional argument. A positional default is simpler and matches the spec's FR-006 ("providing an explicit file or directory path as an argument").

---

### Decision 2: Typer Optional Argument Pattern

**Decision**: Annotate `input_path` as `Path | None = typer.Argument(None)` and resolve to `DEFAULT_INPUT_DIR` inside the command body when `None`.

**Rationale**: Typer >= 0.12 (project uses `>=0.12.0`) supports optional `Argument` values by using `None` as the default and `Optional[Path]` (i.e. `Path | None`) as the type annotation. Passing a non-None `Path` directly as the Argument default also works, but using `None` + explicit resolution in the body makes the intent clearer and gives the command full control over the error message shown when the default path is missing.

```python
input_path: Path | None = typer.Argument(None, help="PNG file or directory (default: /import)")
resolved_input = input_path if input_path is not None else DEFAULT_INPUT_DIR
```

**Alternatives considered**: `Path = typer.Argument(DEFAULT_INPUT_DIR)` — valid but produces a less descriptive `--help` output and makes it harder to distinguish "user supplied default" from "user omitted argument" inside the command body.

---

### Decision 3: Empty-Directory Message Placement

**Decision**: Add an early-exit guard in `_run_batch` (after collecting results) that emits a dedicated "no PNG files found" message and returns with exit code 0.

**Rationale**: `BatchProcessor.process_directory()` already returns `[]` for an empty or all-non-PNG directory. Detecting an empty result list in the CLI layer (before emitting the summary line) is a clean, SRP-compliant addition. The `BatchProcessor` need not be modified — it has no responsibility for user messaging.

The guard reads:
```python
if not results:
    typer.echo(f"No PNG files found in {input_path}.")
    return
```

This satisfies FR-005 (exit 0 + informative message) without altering the `ProcessingResult` model or `BatchProcessor` contract.

---

### Decision 4: Error Message Differentiation

**Decision**: When the resolved input path does not exist, the error message includes the path so users can distinguish between a missing default directory and a bad explicit path.

```
ERROR: /import does not exist.
```

The existing `typer.echo(f"ERROR: {input_path} does not exist.", err=True)` already does this — no change needed, just confirm the message is path-inclusive.

---

## Summary

| Area | Change Needed | Notes |
|------|--------------|-------|
| `cli.py` | Yes — optional `input_path` argument + empty-batch message | Main deliverable |
| `constants.py` | No | `DEFAULT_INPUT_DIR` and `DEFAULT_OUTPUT_DIR` already defined |
| `image_exporter.py` | No | Collision suffix + dir creation already implemented |
| `batch_processor.py` | No | PNG filter + continue-on-fail already implemented |
| `image_processor.py` | No | `ExportError` catch already present |
| `exceptions.py` | No | `ExportError` hierarchy already in place |
| Data model | No | No new entities or status codes required |
