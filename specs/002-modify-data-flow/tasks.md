# Tasks: Modify Data Flow

**Input**: Design documents from `/specs/002-modify-data-flow/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Scope**: Single-file change to `src/cad_image_cropper/cli.py`. All other requirements (collision suffix, output-dir auto-create, non-PNG filtering, continue-on-write-failure) are already implemented.

---

## Phase 1: Foundational (Blocking Prerequisite)

**Purpose**: Update the import in the CLI so `DEFAULT_INPUT_DIR` is available for all subsequent tasks.

**⚠️ CRITICAL**: T001 must complete before any user story work begins.

- [X] T001 Add `DEFAULT_INPUT_DIR` to the constants import line in `src/cad_image_cropper/cli.py`

**Checkpoint**: `DEFAULT_INPUT_DIR` is importable and available in `cli.py`

---

## Phase 2: User Story 1 — Zero-Argument Auto-Processing (Priority: P1) 🎯 MVP

**Goal**: Running `cad-crop` with no arguments automatically reads from `/import` and writes to `/export`.

**Independent Test**: Run `uv run cad-crop` with `/import` mocked as a directory containing PNGs → outputs appear in `/export`; run with empty `/import` → "No PNG files found" message, exit 0; run with missing `/import` → error message, exit 1.

### Implementation

- [X] T002 [US1] Change `input_path` from `Path = typer.Argument(...)` to `Path | None = typer.Argument(None, ...)` and add `resolved_input = input_path if input_path is not None else DEFAULT_INPUT_DIR` in `src/cad_image_cropper/cli.py`
- [X] T003 [US1] Replace all references to `input_path` with `resolved_input` inside the `crop` command body in `src/cad_image_cropper/cli.py`
- [X] T004 [US1] Add early-exit guard `if not results: typer.echo(f"No PNG files found in {resolved_input}."); return` in `_run_batch` in `src/cad_image_cropper/cli.py`

### Tests

- [X] T005 [P] [US1] Add `test_zero_args_processes_import_dir`: invoke CLI with no args, mock `/import` as dir with PNGs, assert results in `/export` in `tests/contract/test_cli_contract.py`
- [X] T006 [P] [US1] Add `test_zero_args_empty_import_dir`: invoke CLI with no args, mock `/import` as empty dir, assert "No PNG files found" in output, assert exit 0 in `tests/contract/test_cli_contract.py`
- [X] T007 [P] [US1] Add `test_zero_args_missing_import_dir`: invoke CLI with no args, ensure `/import` absent, assert error message in stderr, assert exit 1 in `tests/contract/test_cli_contract.py`

**Checkpoint**: `uv run cad-crop` (no args) fully functional and all three US1 tests pass

---

## Phase 3: User Story 2 — Explicit Input Path Override (Priority: P2)

**Goal**: Existing explicit-path invocations (`cad-crop /some/path`) continue to work unchanged.

**Independent Test**: Run `cad-crop /some/explicit/dir` and `cad-crop /some/file.png` — behavior identical to before this feature.

### Tests

- [X] T008 [P] [US2] Add `test_explicit_dir_path_still_works`: invoke CLI with explicit directory path, assert same behavior as before in `tests/contract/test_cli_contract.py`
- [X] T009 [P] [US2] Add `test_explicit_file_path_still_works`: invoke CLI with explicit single PNG file path, assert same behavior as before in `tests/contract/test_cli_contract.py`
- [X] T010 [P] [US2] Add `test_explicit_nonexistent_path_exits_1`: invoke CLI with non-existent explicit path, assert exit 1 and error message in `tests/contract/test_cli_contract.py`

**Checkpoint**: All explicit-path invocations verified to work; all US2 tests pass

---

## Phase 4: User Story 3 — Explicit Output Directory Override (Priority: P3)

**Goal**: The `--output-dir` option continues to write results to the specified directory instead of `/export`.

**Independent Test**: Run `cad-crop --output-dir /tmp/results` → cropped files appear in `/tmp/results`, not `/export`.

### Tests

- [X] T011 [P] [US3] Add `test_output_dir_override_writes_to_custom_dir`: invoke CLI with `--output-dir /tmp/results`, assert output files in specified dir and not in `/export` in `tests/contract/test_cli_contract.py`
- [X] T012 [P] [US3] Add `test_output_dir_autocreated_if_absent`: invoke CLI with `--output-dir` pointing to non-existent path, assert dir is created and file written in `tests/contract/test_cli_contract.py`

**Checkpoint**: `--output-dir` override verified; all US3 tests pass

---

## Phase 5: Polish & Quality Gates

**Purpose**: Ensure zero linting/type violations and validate end-to-end behaviour.

- [X] T013 Run `uv run ruff check src/ tests/` and fix any violations introduced in `src/cad_image_cropper/cli.py`
- [X] T014 Run `uv run mypy src/` and fix any type errors (ensure `Path | None` annotation satisfies mypy --strict) in `src/cad_image_cropper/cli.py`
- [X] T015 Run the quickstart.md validation checklist end-to-end (all 8 items) and confirm all pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — start immediately
- **User Story 1 (Phase 2)**: Depends on T001
- **User Story 2 (Phase 3)**: Depends on T001, T002, T003 (needs optional arg in place to test override)
- **User Story 3 (Phase 4)**: Depends on T001, T002, T003
- **Polish (Phase 5)**: Depends on all story phases

### Within User Story 1

- T001 → T002 → T003 → T004 (sequential — all in same file)
- T005, T006, T007 [P] — can be written in parallel after T004

### Parallel Opportunities

- T005, T006, T007 (US1 tests) — parallel after T004
- T008, T009, T010 (US2 tests) — parallel, after T003
- T011, T012 (US3 tests) — parallel, after T003
- T013, T014 — parallel (different tools, same file)

---

## Parallel Execution Example: User Story 1

```bash
# After T001–T004 complete, launch test tasks in parallel:
Task: "test_zero_args_processes_import_dir in tests/contract/test_cli_contract.py"  # T005
Task: "test_zero_args_empty_import_dir in tests/contract/test_cli_contract.py"      # T006
Task: "test_zero_args_missing_import_dir in tests/contract/test_cli_contract.py"    # T007
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: T001
2. Complete Phase 2: T002 → T003 → T004, then T005/T006/T007
3. **STOP and VALIDATE**: `uv run cad-crop` works with no args
4. Run Polish: T013, T014 against cli.py only

### Incremental Delivery

1. Phase 1 + Phase 2 → zero-arg workflow works (MVP)
2. Phase 3 → backward-compat verified with tests
3. Phase 4 → `--output-dir` confirmed with tests
4. Phase 5 → full quality gate

---

## Notes

- Only `src/cad_image_cropper/cli.py` is modified; all other source files are unchanged
- `[P]` test tasks write to the same file (`test_cli_contract.py`) but are independent functions — coordinate to avoid merge conflicts when working in parallel
- All existing tests must continue to pass after T002–T004
- Commit after Phase 2 checkpoint (MVP) and after Phase 5 (final)
