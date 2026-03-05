# Feature Specification: Image Detection and Cropping — Left Panel Border Crop

**Feature Branch**: `004-crop-left-panel`
**Created**: 2026-03-05
**Status**: Draft
**Input**: User description: "Image Detection and Cropping Issue: Exported output images are not cropped. Detect left wide panel by height-weight bold black border and crop only that panel."

## Clarifications

### Session 2026-03-05

- Q: Should the new bold-border detection replace the separator-line approach entirely, or run as a combined pipeline? → A: Replace entirely — bold-border detection replaces the separator-line approach; `ClassicalBorderDetector` is rewritten to detect border rectangles.
- Q: When multiple qualifying bordered panels are found, what is the primary selection rule? → A: Widest panel — select the bordered panel with the greatest width; use left-edge position as tiebreaker.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Detect and Crop to the Main Drawing Panel (Priority: P1)

A user processes a CAD floor plan image. The image contains a main drawing panel enclosed by a tall, thick black rectangular border, with a title block and margins outside that border. The system detects this bordered panel, crops the output to exactly that bounding box, and exports the result. Currently the output is not cropped — it exports the full image unchanged.

**Why this priority**: This is the core defect. Without correct panel detection and cropping, the tool produces no useful output. Every other story depends on this working correctly.

**Independent Test**: Process a single CAD floor plan PNG with a clearly visible thick black border. The exported output should contain only the panel interior and its border — no title block, no outer margin.

**Acceptance Scenarios**:

1. **Given** a CAD floor plan PNG with a main drawing panel enclosed by a bold black rectangular border, **When** the image is processed, **Then** the exported output is cropped to the bounding box of that bordered panel, excluding all content outside the border.
2. **Given** a CAD floor plan PNG where the bold-bordered panel is on the left side of the image, **When** the image is processed, **Then** the output shows only that panel — no title block columns or outer margins are visible on any edge.
3. **Given** the cropped output image, **When** inspected, **Then** all four border lines of the drawing panel are visible at the edges of the output, confirming the crop is tight to the panel border.

---

### User Story 2 — Select the Left Wide Panel When Multiple Bordered Regions Exist (Priority: P1)

A CAD image may contain more than one bordered region — for example, a large drawing panel on the left and a smaller title block on the right. The system must identify and select the correct panel: the bordered rectangle with the greatest width (left-edge position used as tiebreaker only).

**Why this priority**: Without correct selection logic, the tool may crop to a title block sub-panel or a small annotation box instead of the main floor plan. This is as critical as detection itself.

**Independent Test**: Process an image with two rectangular bordered regions of different widths. Confirm the output corresponds to the wider, left-side region.

**Acceptance Scenarios**:

1. **Given** a CAD image with a wide main drawing panel on the left and a narrow title block panel on the right, **When** processed, **Then** the output is cropped to the wide left panel, not the narrow title block.
2. **Given** a CAD image where only one bordered panel exists, **When** processed, **Then** the output is cropped to that single panel regardless of its position.

---

### User Story 3 — Skip Images Where No Qualifying Panel Is Detected (Priority: P2)

If the system cannot locate a panel that meets the detection criteria (bold black border, sufficient height and width), it must skip the image rather than exporting an uncropped or incorrectly cropped result.

**Why this priority**: Exporting a full uncropped image as if it were a successful crop is misleading. A clear skip with a log message is preferable.

**Independent Test**: Process a blank image with no bold border rectangle. Confirm no output file is created and the result status is "skipped".

**Acceptance Scenarios**:

1. **Given** a PNG with no thick black rectangular border, **When** processed, **Then** no output file is created and the result status is "skipped — no panel detected".
2. **Given** a PNG where bordered regions exist but none are wide or tall enough to qualify as a main drawing panel, **When** processed, **Then** the image is skipped rather than producing a wrong crop.

---

### Edge Cases

- What happens when the bold border is partially clipped by the image boundary (edge of scanned page)?
- How does the system handle low-contrast scans where the border appears grey rather than solid black?
- What if there are thick internal room walls that resemble the outer border?
- What happens when the border thickness varies — bold on two sides and thinner on others?
- How does the system handle images where the panel occupies nearly the full page with minimal margin?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST detect the main drawing panel in a CAD floor plan image by identifying a closed rectangular region enclosed by a tall, thick (bold) black border on all four sides. This approach replaces the prior separator-line detection method entirely.
- **FR-002**: System MUST crop the output image to the bounding box of the detected drawing panel border, inclusive of the border lines themselves.
- **FR-003**: When multiple bordered rectangular regions are present, System MUST select the one with the greatest width; if two panels share equal width, the one with the smaller left-edge x-coordinate is chosen.
- **FR-004**: System MUST skip and not export any image for which no qualifying drawing panel border is detected; the processing result MUST report the image as skipped.
- **FR-005**: System MUST preserve the original image DPI metadata in the cropped output.
- **FR-006**: System MUST distinguish the drawing panel border (thick outer frame) from thinner internal lines within the drawing (wall lines, dimension lines, annotation boxes).
- **FR-007**: System MUST log whether a panel was detected and what bounding box coordinates were used, to enable diagnosis of detection failures.

### Key Entities

- **Drawing Panel**: The main floor plan region enclosed by a bold rectangular black border. Characterised by: near-full image height, widest bordered region in the image, positioned on the left side.
- **Panel Border**: The thick black rectangular frame that defines the boundary of the drawing panel. The primary detection target.
- **Crop Region**: The axis-aligned bounding box of the detected panel border, defining the output image extent.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of CAD floor plan images containing a clearly visible thick black rectangular drawing panel border are successfully detected and cropped.
- **SC-002**: The cropped output shows no title block content — all four edges of the output image fall on or within the drawing panel border.
- **SC-003**: Images with no qualifying drawing panel border produce zero output files and are explicitly reported as skipped.
- **SC-004**: All previously passing automated tests continue to pass with no regressions introduced.
- **SC-005**: Processing time per image does not exceed 30 seconds on a standard workstation.

## Assumptions

- "Height-weight bold black border" in the description is interpreted as a **tall, thick (heavy-weight) black rectangular border** — the outer frame of the main drawing area, not interior room walls.
- The drawing panel is selected as the **widest** bordered rectangle in the image; left-edge position is a tiebreaker only. This is consistent with standard Korean/Japanese CAD floor plan layouts where the title block is a narrow vertical strip on the right and the drawing panel is always wider.
- The crop output includes the border lines themselves (the outer edge of the border becomes the edge of the output image).
- The bold border is substantially thicker than interior lines (wall lines, dimension lines) — thickness is the primary discriminator between the panel border and internal drawing content.
- A "qualifying" panel must span at least 50% of the image height and 40% of the image width to be considered the main drawing panel, not a small annotation or title sub-box.
- Input images are always PNG format at the original scan DPI, consistent with existing tool conventions.
- The bold-border detection approach fully replaces the separator-line approach from feature 003; no fallback to the old method is provided.
