# Implementation Plan: Modify Data Flow

**Branch**: `002-modify-data-flow` | **Date**: 2026-03-04 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/002-modify-data-flow/spec.md`

---

## Summary

Make `INPUT_PATH` an optional CLI argument that defaults to `/import`, and emit a clear human-readable message when the input directory contains no PNG files. All other requirements (collision suffix, output-dir auto-create, non-PNG filtering, continue-on-write-failure) are already implemented by the existing `ImageExporter` and `BatchProcessor` classes. The net code change is a two-part modification to `cli.py` only.

---

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: Typer >= 0.12 (CLI), Pillow >= 11 (PNG I/O), existing services
**Storage**: Filesystem only — `/import` (read), `/export` (write)
**Testing**: pytest, ruff check, mypy --strict
**Target Platform**: Linux (OS-agnostic Path usage)
**Project Type**: CLI tool
**Performance Goals**: N/A — no performance-sensitive path changed
**Constraints**: Full backward compatibility; all existing explicit-path invocations must continue to work unchanged
**Scale/Scope**: Single CLI command; single source file change

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Object-Oriented Design | PASS | All changes remain within existing class boundaries; no bare procedural logic added |
| II. SOLID | PASS | SRP maintained — CLI still only parses and delegates; no new responsibilities |
| III. DRY | PASS | `DEFAULT_INPUT_DIR` constant reused; no duplication of path logic |
| IV. Clean Code & Naming | PASS | `resolved_input` conveys intent; no magic strings |
| V. SRP per Method | PASS | `_run_batch` gains one early-exit guard (≤ 3 lines); stays well under 20 lines |
| VI. Error Handling | PASS | Input-path existence check retained; `ExportError` path unchanged |

No violations. Complexity Tracking table not required.

---

## Project Structure

### Documentation (this feature)

```text
specs/002-modify-data-flow/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   └── cli-contract.md  ← Phase 1 output (supersedes 001 contract)
└── tasks.md             ← Phase 2 output (/speckit.tasks — not created here)
```

### Source Code (repository root)

```text
src/cad_image_cropper/
├── cli.py              ← MODIFIED (only file changed)
├── constants.py        ← unchanged (DEFAULT_INPUT_DIR already defined)
├── services/
│   ├── image_exporter.py   ← unchanged (collision suffix already implemented)
│   └── batch_processor.py  ← unchanged (PNG filter already implemented)
└── [all other modules]     ← unchanged

tests/
├── unit/
│   └── test_services.py         ← unchanged
├── contract/
│   └── test_cli_contract.py     ← EXTENDED (zero-arg invocation, empty-dir, missing-dir)
└── integration/
    └── test_pipeline.py         ← unchanged
```

**Structure Decision**: Single-project layout (Option 1). The feature touches only the CLI entry point; no new modules or packages are created.

---

## Phase 0 — Research

*See [research.md](research.md) for full findings.*

**Key finding**: The scope is narrower than anticipated. Five of nine functional requirements are already satisfied by existing code. Only `cli.py` changes.

**Resolved unknowns**:

| Unknown | Resolution |
|---------|-----------|
| Typer optional argument pattern | `Path \| None = typer.Argument(None)` with in-body resolution to `DEFAULT_INPUT_DIR` |
| Empty-directory detection point | CLI layer (`_run_batch`) — after `process_directory()` returns `[]` |
| Backward compatibility risk | Zero — explicit path still accepted as before; only the `...` sentinel changes to `None` |

---

## Phase 1 — Design & Contracts

### CLI Argument Change (FR-001)

**File**: `src/cad_image_cropper/cli.py`

**Before**:
```python
@app.command()
def crop(
    input_path: Path = typer.Argument(..., help="PNG file or directory of PNG files"),
    ...
```

**After**:
```python
@app.command()
def crop(
    input_path: Path | None = typer.Argument(None, help="PNG file or directory of PNG files (default: /import)"),
    ...
```

**Resolution in command body**:
```python
resolved_input = input_path if input_path is not None else DEFAULT_INPUT_DIR
```

All subsequent references to `input_path` become `resolved_input`.

### Empty-Directory Message (FR-005, SC-005)

**File**: `src/cad_image_cropper/cli.py` → `_run_batch`

Add before the counting loop:
```python
if not results:
    typer.echo(f"No PNG files found in {input_path}.")
    return
```

This satisfies the exit-0 requirement (no `raise typer.Exit`) and replaces the uninformative `Processed: 0 | Skipped: 0 | Failed: 0` message.

### Imports

Add `DEFAULT_INPUT_DIR` to the existing constants import line:
```python
from cad_image_cropper.constants import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR
```

### Contract Update

The CLI contract is superseded — see [contracts/cli-contract.md](contracts/cli-contract.md).
`INPUT_PATH` changes from required to optional (bracketed in `--help` output).

### Test Additions

New contract tests in `tests/contract/test_cli_contract.py`:

| Test | Scenario | Expected |
|------|----------|----------|
| `test_zero_args_uses_import_dir` | No arguments; `/import` mocked as dir with PNGs | Processes files, exits 0 |
| `test_zero_args_empty_import_dir` | No arguments; `/import` mocked as empty dir | "No PNG files found" message, exits 0 |
| `test_zero_args_missing_import_dir` | No arguments; `/import` does not exist | Error message, exits 1 |
| `test_explicit_path_still_works` | Existing explicit-path invocation | Unchanged behavior |

---

## Phase 2 — Tasks

*Generated by `/speckit.tasks` — not part of this command's output.*

---

## Complexity Tracking

*No violations — table not required.*
