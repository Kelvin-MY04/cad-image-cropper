# Feature Specification: CAD Floor Plan Panel Crop

**Feature Branch**: `001-floor-plan-crop`
**Created**: 2026-03-04
**Status**: Draft

## Clarifications

### Session 2026-03-04

- Q: When no border is detected in an image, what should the system do? → A: Skip the file,
  emit a warning with the filename, and continue processing remaining files.
- Q: When the AI model detects a border with low confidence, should the system try a classical
  fallback before skipping? → A: Yes — attempt classical line detection as a fallback; use
  its result if a border is found, otherwise skip and warn.
- Q: If the HuggingFace model cannot be downloaded, should the system abort or continue?
  → A: Proceed using classical line detection only and warn the user that the model is
  unavailable.
- Q: When an output file with the same name already exists in the output directory, what
  should the system do? → A: Write a renamed copy with a numeric suffix (e.g.,
  `floor_plan_1.png`, `floor_plan_2.png`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Single Image Panel Crop (Priority: P1)

A user has a PNG file of a CAD floor plan where the full floor plan view occupies the left
portion of the image and a detail/legend panel occupies the right portion. The two areas are
visually separated by a dark, bold vertical border. The user processes the image and receives
a new PNG file containing only the left floor plan area, at exactly the same pixel dimensions,
resolution, and DPI as the original.

**Why this priority**: This is the core value of the tool. Without it no other story is useful.

**Independent Test**: Supply a known sample floor plan PNG, run the tool, verify that the
output file contains only the floor plan region and that width, height, and DPI metadata
match the input file exactly.

**Acceptance Scenarios**:

1. **Given** a valid floor plan PNG with a right-side detail panel separated by a dark bold
   border, **When** the user runs the tool with that file as input, **Then** the output PNG
   contains only the left floor plan region with no right panel remnants.

2. **Given** the same input file, **When** the output is produced, **Then** the output file's
   pixel width and height match the cropped region exactly and its DPI metadata equals the
   input DPI.

3. **Given** an input PNG where the border detection model locates the separator correctly,
   **When** the crop is applied, **Then** the separator border line itself is not included in
   the output image.

---

### User Story 2 - Batch Processing Multiple Images (Priority: P2)

A user has a directory containing multiple CAD floor plan PNG files, all following the same
two-panel layout. The user processes the entire directory in one operation and receives
cropped output files for every image in the batch.

**Why this priority**: Engineers and architects routinely work with sets of floor plan sheets;
single-file processing would not scale to real project volumes.

**Independent Test**: Supply a directory of 5 sample PNG files, run the tool in batch mode,
verify 5 output PNG files are produced, each correctly cropped.

**Acceptance Scenarios**:

1. **Given** a directory of N valid floor plan PNGs, **When** the user points the tool at the
   directory, **Then** N output files are produced, each correctly cropped.

2. **Given** a batch that includes one file where no border is detected, **When** the tool
   runs, **Then** it skips that file, emits a warning message identifying the filename, and
   continues processing the remaining files without stopping.

3. **Given** a batch that includes one invalid or corrupt PNG file, **When** the tool runs,
   **Then** it reports the failure for that file and continues processing the remaining files
   without stopping.

---

### User Story 3 - Output Path Control (Priority: P3)

A user wants cropped images saved to a specific output location instead of alongside the
input files. The user specifies an output directory and the tool saves all results there,
preserving original file names.

**Why this priority**: Keeping output separate from the source is standard workflow hygiene
and prevents accidental overwriting of originals.

**Independent Test**: Run the tool with an explicit output directory argument; verify output
files appear in that directory and the input directory is unchanged.

**Acceptance Scenarios**:

1. **Given** an output directory is specified, **When** the tool completes, **Then** all
   output files appear in the specified directory and original input files are unmodified.

2. **Given** a specified output directory that does not yet exist, **When** the tool runs,
   **Then** the directory is created automatically before writing output files.

---

### Edge Cases

- No border detected: the file is skipped and a warning naming the file is emitted; no
  output file is produced for that image.
- Low-confidence model detection: the system attempts a classical line-detection fallback;
  if that confirms a border, the crop proceeds; if no border is confirmed, the file is
  skipped and a warning is emitted.
- What happens when the right panel occupies more than 50% of the image width?
- What happens when the input file is not a valid PNG (corrupt, wrong format)?
- What happens when the input image resolution is very low (border not distinguishable)?
- What happens when multiple vertical borders exist in the image?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST accept a single PNG file path as input.
- **FR-002**: The system MUST accept a directory path as input and process all PNG files
  within it.
- **FR-003**: The system MUST detect the dark bold vertical border separating the left floor
  plan region from the right detail panel using a two-stage strategy: primary detection via
  the HuggingFace model, followed by classical line detection as a fallback when the model
  confidence is below an acceptable threshold.
- **FR-004**: The system MUST crop the image to retain only the content to the left of the
  detected border.
- **FR-005**: The output PNG MUST have the same DPI metadata as the input file.
- **FR-006**: The output PNG MUST have pixel dimensions equal to the cropped region (width
  reduced to the left region; height unchanged).
- **FR-007**: The system MUST attempt to load a pre-trained image detection model sourced
  from HuggingFace as the primary border detection method.
- **FR-007a**: When the HuggingFace model produces a low-confidence result, the system MUST
  attempt classical line detection as a secondary fallback to confirm or locate the border.
- **FR-007b**: If the HuggingFace model cannot be downloaded or loaded, the system MUST emit
  a warning that the model is unavailable and proceed using classical line detection as the
  sole detection method for the entire run.
- **FR-008**: When neither the model nor the classical fallback detects a border, the system
  MUST skip that image, emit a descriptive warning that includes the filename, and continue
  processing any remaining files in the batch.
- **FR-009**: The system MUST accept an optional output directory parameter; when omitted,
  output files MUST be written to a default `output/` directory relative to the working
  directory.
- **FR-010**: The system MUST use the original filename for each output file. If a file with
  that name already exists in the output directory, the system MUST write a renamed copy by
  appending an incrementing numeric suffix before the file extension
  (e.g., `floor_plan.png` → `floor_plan_1.png` → `floor_plan_2.png`).
- **FR-011**: The system MUST NOT overwrite the original input file.
- **FR-012**: The system MUST support processing images where the border position varies
  across different files in a batch.

### Key Entities

- **Input Image**: A PNG file representing a CAD floor plan with a two-panel layout. Key
  attributes: file path, pixel width, pixel height, DPI.
- **Border**: The dark, bold vertical line in the image that separates the floor plan region
  from the detail panel. Key attributes: horizontal pixel position (x-coordinate), confidence
  score from the detection model.
- **Cropped Region**: The left portion of the input image from pixel 0 to the border
  x-coordinate. Inherits DPI from the input image.
- **Output Image**: The exported PNG of the cropped region. Key attributes: file path, pixel
  dimensions matching the cropped region, DPI matching input.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The tool correctly identifies and removes the right detail panel in at least
  95% of valid floor plan PNG inputs in a representative test set.
- **SC-002**: The output PNG's DPI metadata matches the input PNG's DPI metadata in 100%
  of processed files.
- **SC-003**: The output PNG pixel dimensions equal the width of the detected left region and
  the full height of the input, verified against ground-truth crop coordinates in 100% of
  test cases.
- **SC-004**: A batch of 50 floor plan images completes processing within 5 minutes on
  standard desktop hardware.
- **SC-005**: When processing a batch that contains one undetectable-border file, the tool
  skips it with a warning, completes all other files, and exits without crashing.
- **SC-006**: A user unfamiliar with the tool can process their first image correctly using
  only the help output, without consulting external documentation.

## Assumptions

- Input images follow a consistent two-panel horizontal layout: floor plan on the left,
  detail/legend panel on the right.
- The separator border is always vertical (not horizontal) and is visually darker and bolder
  than internal drawing lines.
- Input files are PNG format; other image formats are out of scope for this feature.
- The HuggingFace model will be downloaded automatically on first run and cached locally for
  subsequent executions. If the download fails, the tool degrades gracefully to classical
  line detection only and warns the user.
- Users run the tool from a command-line interface; no graphical user interface is required
  for this feature.
- The cropped output does not need to pad the image back to the original full width — the
  output width equals the width of the left region only.
