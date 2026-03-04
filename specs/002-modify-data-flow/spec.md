# Feature Specification: Modify Data Flow

**Feature Branch**: `002-modify-data-flow`
**Created**: 2026-03-04
**Status**: Draft
**Input**: User description: "Modify Data flow: Modify the features of importing and exporting image files. Make sure to detect automatically /import folder and export automatically in /export directory as default."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Zero-Argument Auto-Processing (Priority: P1)

A user places PNG files into the `/import` folder and runs the tool without any arguments. The tool automatically discovers all PNG files in `/import`, processes them, and writes cropped outputs to `/export`. The user does not need to specify paths.

**Why this priority**: This is the primary UX improvement. Eliminating mandatory path arguments reduces friction and aligns the tool with a zero-configuration drop-folder workflow. Without this, the rest of the feature has little value.

**Independent Test**: Can be fully tested by running the CLI with no arguments while `/import` contains PNG files, and verifying that cropped results appear in `/export`.

**Acceptance Scenarios**:

1. **Given** `/import` exists and contains one or more PNG files, **When** the user runs the tool with no arguments, **Then** the tool processes all PNG files and writes outputs to `/export`.
2. **Given** `/import` exists but is empty, **When** the user runs the tool with no arguments, **Then** the tool exits with code 0 and displays a message indicating no files were found.
3. **Given** `/import` does not exist, **When** the user runs the tool with no arguments, **Then** the tool reports a clear error that the default input folder is missing and exits with a non-zero code.

---

### User Story 2 - Explicit Input Path Override (Priority: P2)

A user wants to process images from a non-default location. They supply a custom input path (file or directory) as an argument. The tool uses that path instead of `/import`, and still defaults output to `/export` unless overridden.

**Why this priority**: Preserves backward compatibility and supports ad-hoc use cases. Without this, users working with images outside `/import` are blocked.

**Independent Test**: Can be fully tested by running the CLI with an explicit input path and verifying the correct files are processed regardless of `/import` contents.

**Acceptance Scenarios**:

1. **Given** a user provides a valid directory path as input, **When** the tool runs, **Then** PNG files from that directory are processed and results go to `/export`.
2. **Given** a user provides a valid single PNG file path as input, **When** the tool runs, **Then** that file is processed and the result goes to `/export`.
3. **Given** a user provides an invalid or non-existent path as input, **When** the tool runs, **Then** the tool reports a clear error and exits with a non-zero code.

---

### User Story 3 - Explicit Output Directory Override (Priority: P3)

A user wants to send processed images to a non-default location. They supply a custom output directory. The tool writes all results to that directory instead of `/export`.

**Why this priority**: Supports integration into larger pipelines where output location is externally controlled.

**Independent Test**: Can be fully tested by specifying `--output-dir` to a writable directory and verifying cropped files appear there, not in `/export`.

**Acceptance Scenarios**:

1. **Given** a user provides a valid writable directory via `--output-dir`, **When** the tool runs, **Then** all cropped images are written to that directory.
2. **Given** the specified output directory does not exist, **When** the tool runs, **Then** the tool creates it automatically and writes outputs there.

---

### Edge Cases

- What happens when `/import` contains a mix of PNG and non-PNG files? Non-PNG files are silently ignored; only `.png` files are processed.
- What happens when `/export` does not exist? The tool creates `/export` automatically before writing any output.
- What happens when a PNG file in `/import` is unreadable or corrupt? The file is skipped with a warning; other files continue processing.
- What happens when the user provides both an explicit input path and no output path? Output defaults to `/export`.
- What happens when `/import` contains subdirectories? Only PNG files at the top level of the directory are processed (no recursive scanning assumed, consistent with current batch behavior).
- What happens when an output file with the same name already exists in the output directory? The tool appends a numeric suffix to the filename (e.g., `floor-plan_1.png`, `floor-plan_2.png`) until a non-conflicting name is found; the existing file is never overwritten.
- What happens when writing an output file fails (disk full, permission denied)? The file is skipped with a warning message; remaining files in the batch continue to be processed.

## Clarifications

### Session 2026-03-04

- Q: When an output file with the same name already exists in the output directory, what should the tool do? → A: Rename with suffix — write as `filename_1.png`, `filename_2.png`, etc.
- Q: When writing an output file fails (disk full, permissions), should the batch abort or continue? → A: Skip and warn — log the failure and continue processing remaining files.
- Q: When the tool finds no PNG files to process, what should the exit code be? → A: Exit 0 — "no files found" is a normal, expected outcome, not an error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When no input path is provided, the system MUST automatically use `/import` as the input source.
- **FR-002**: When no output directory is provided, the system MUST automatically write results to `/export`.
- **FR-003**: The system MUST create the output directory if it does not already exist.
- **FR-004**: When `/import` is used as default input and does not exist, the system MUST report a descriptive error and exit with a non-zero status code.
- **FR-005**: When `/import` is used as default input and is empty (no PNG files), the system MUST exit with code 0 and display an informative message indicating no files were found.
- **FR-006**: The system MUST allow users to override the input source by providing an explicit file or directory path as an argument.
- **FR-007**: The system MUST allow users to override the output directory via a command-line option.
- **FR-008**: Non-PNG files in the input directory MUST be silently ignored during batch processing.
- **FR-009**: All existing single-file and batch processing behaviors MUST be preserved when explicit paths are provided.
- **FR-010**: When an output file with the same name already exists in the output directory, the system MUST write the new file with a numeric suffix (e.g., `filename_1.png`, `filename_2.png`) rather than overwriting the existing file.
- **FR-011**: When writing an output file fails (e.g., insufficient disk space, permission denied), the system MUST log a warning for that file and continue processing all remaining files in the batch.

### Key Entities

- **Import Folder** (`/import`): The default watched source directory where users place PNG files for processing. Resolved relative to the filesystem root by default.
- **Export Folder** (`/export`): The default output directory where cropped PNG files are written. Created automatically if absent.
- **Processing Session**: A single invocation of the tool that reads from one input source and writes all results to one output directory.

## Assumptions

- The `/import` and `/export` paths are absolute paths rooted at the filesystem root (not relative to the working directory).
- No recursive directory scanning is required — only top-level PNG files in the input directory are processed.
- The tool is always run manually by a user or script; no filesystem watching or daemon mode is in scope.
- Output filenames are based on the input filename; when a collision occurs, a numeric suffix is appended (`_1`, `_2`, etc.) until a free name is found.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can process all PNG files in `/import` by running the tool with zero arguments — no path specification required.
- **SC-002**: 100% of invocations without an explicit output path write results to `/export`.
- **SC-003**: The output directory is created automatically in 100% of cases where it does not pre-exist.
- **SC-004**: Users who previously supplied explicit paths experience no change in behavior — all existing invocation patterns continue to work.
- **SC-005**: Informative, human-readable messages are displayed when the default input folder is missing or empty, enabling users to self-diagnose without consulting documentation.
