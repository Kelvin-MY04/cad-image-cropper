# Feature Specification: Fix Panel Detection and Cropping

**Feature Branch**: `003-fix-panel-crop`
**Created**: 2026-03-05
**Status**: Draft
**Input**: User description: "Debug Implementation: Detecting and Cropping the image is still not correct yet. Sample input is a CAD floor plan sheet with a title block panel on the right side. Sample output shows the floor plan cropped to remove the title block, keeping only the drawing area. Current output is totally different from the expected sample output."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Accurate Title Block Removal (Priority: P1)

A user processes a CAD floor plan sheet image. The sheet has a floor plan drawing on the left portion and a title block panel (containing project info, stamps, revision history) on the right side. The system must detect where the drawing area ends and the title block begins, then crop the image to keep only the drawing area.

**Why this priority**: This is the core purpose of the tool — producing a correctly cropped output. Without this, all output is wrong.

**Independent Test**: Process `test/sample/input.png` through the pipeline and compare the output against `test/sample/output.png`. The two images must be visually equivalent: same floor plan content, no title block visible, similar bounding margins.

**Acceptance Scenarios**:

1. **Given** a CAD floor plan PNG where the title block occupies the rightmost 10–25% of the image width as a vertically full-height panel, **When** the image is processed, **Then** the output image contains only the drawing area to the left of the title block separator line.
2. **Given** the sample input `test/sample/input.png`, **When** processed, **Then** the output visually matches `test/sample/output.png` with the right-side title block removed and the floor plan drawing fully retained.
3. **Given** the sample input, **When** the detector runs, **Then** the detected x-coordinate falls within the drawing-to-title-block separator zone (right 10–30% of image width), not within the interior drawing lines.

---

### User Story 2 - Correct Detection Target: Full-Height Separator Line (Priority: P1)

The detection algorithm must specifically target the full-height vertical separator line that runs the entire height of the document, separating the drawing from the title block — not the interior vertical lines of the floor plan (walls, grid lines, dimension markers).

**Why this priority**: The root cause of the current failure is that the algorithm selects the most common vertical line position, which happens to be interior drawing lines rather than the title block separator. This story fixes the detection target.

**Independent Test**: The detector should return an x-coordinate in the right 10–30% of the image width, consistent with the separator line position visible in the sample input.

**Acceptance Scenarios**:

1. **Given** a CAD image with many short interior vertical lines and one dominant full-height vertical separator, **When** detection runs, **Then** the detected x-coordinate corresponds to the full-height separator, not interior lines.
2. **Given** the sample input image, **When** the classical detector runs, **Then** it returns an x-coordinate approximately matching the visible title block boundary (~70–90% of image width from left).
3. **Given** an image with no title block separator, **When** detection runs, **Then** the system returns a "no border detected" result and skips the image.

---

### User Story 3 - Output Preserves Drawing Margin (Priority: P2)

The cropped output must include the natural whitespace/margin that surrounds the floor plan drawing, preserving readability. The crop boundary is the separator line itself, not a tight fit around the drawn content.

**Why this priority**: Cropping too tightly at the drawing lines produces visually incorrect output (cuts off dimension annotations, outer walls, etc.).

**Independent Test**: Crop region x_end equals the detected separator x-coordinate. No additional inset trimming is applied.

**Acceptance Scenarios**:

1. **Given** a detected separator at x-position X, **When** the image is cropped, **Then** the crop box is `(0, 0, X, height)` — no padding subtracted from x.
2. **Given** the sample output image, **When** compared to the crop of the sample input at the separator line, **Then** the outer dimension annotations and margins are fully visible.

---

### Edge Cases

- What happens when the image has no title block (only floor plan)? → No separator detected; image is skipped with `SKIPPED_NO_BORDER` status.
- What happens when the separator line is very close to the right edge (top 5% of width from right)? → Excluded; a minimum title block width threshold prevents trivial edge detections.
- What happens when multiple full-height vertical lines exist (e.g., multi-column title blocks)? → The leftmost qualifying full-height line in the right-side zone is selected (the boundary closest to the drawing area).
- What happens if the image is grayscale (black-and-white PDF conversion)? → Algorithm must handle both RGB and grayscale inputs without error.
- What happens when the separator line has minor gaps due to PDF rendering artifacts? → Lines spanning ≥ 70% of image height are still accepted as qualifying separators.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The detector MUST identify the vertical line separating the drawing area from the title block panel by targeting lines that span most (≥ 70%) of the image height, excluding shorter interior drawing elements.
- **FR-002**: The detector MUST search for the separator in the right-side zone of the image (right 10–30% of width) and select the leftmost qualifying full-height line in that zone, not the most frequently occurring vertical x-position across the whole image.
- **FR-003**: The crop region MUST use the detected separator x-coordinate as the right boundary, producing a crop box of `(0, 0, separator_x, image_height)`.
- **FR-004**: The edge exclusion margin MUST apply only on the LEFT edge (≤ 5% of width from left) to avoid cropping at the drawing's own outer border; the right-side search zone explicitly targets the title block separator.
- **FR-005**: The detector MUST handle both RGB and grayscale input images without error.
- **FR-006**: When no qualifying separator line is detected, the system MUST return a `DetectionMethod.NONE` result and emit a `SKIPPED_NO_BORDER` processing status.
- **FR-007**: The output image MUST preserve the original DPI metadata from the source PNG.
- **FR-008**: The detection algorithm MUST NOT write any image files to disk; file I/O remains exclusively in the service layer.

### Key Entities

- **Separator Line**: The full-height vertical line in the right zone of a CAD sheet that delineates the drawing panel from the title block panel. Characterized by: near-full image height span (≥ 70%), located in the rightmost 10–30% of image width.
- **Drawing Area**: The region to the left of the separator line containing the floor plan, dimensions, notes, and surrounding whitespace margin.
- **Title Block Panel**: The region to the right of the separator containing project metadata, revision history, stamps, and approval signatures.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Processing `test/sample/input.png` produces an output whose width is within ±5% of `test/sample/output.png`'s width — the title block is absent and the full floor plan drawing is retained. Validation is performed by comparing output image width against expected image width (dimension comparison, not pixel-level match).
- **SC-002**: The detected separator x-coordinate falls within the right 10–30% of the image width (i.e., between 70%–90% of total width) for standard CAD sheets with a title block.
- **SC-003**: The detected x-coordinate does NOT fall in the interior drawing zone (left 70% of image width), which was the failure mode of the previous implementation.
- **SC-004**: All existing test cases that previously passed continue to pass (no regressions).
- **SC-005**: The pipeline processes the sample image end-to-end in under 30 seconds on standard hardware using the classical detection path.

## Clarifications

### Session 2026-03-05

- Q: How should SC-001 "visually matches test/sample/output.png" be validated in automated testing? → A: Output width must be within ±5% of the expected output's width (dimension comparison, not pixel-level match).
- Q: What is the intended scope for the SAM-based fallback detector in this fix? → A: SAM detector is out of scope — fix applies to ClassicalBorderDetector only; SAM addressed separately if needed.

## Assumptions

- **A-001**: The title block separator is always a single, full-height vertical line positioned in the right 10–30% of the sheet width. Layouts where the title block is on the left, top, or bottom are out of scope.
- **A-002**: The input images are PNG files converted from CAD/PDF drawings with standard A-series or ANSI sheet proportions.
- **A-003**: The separator line is visually solid (black, continuous) and spans the full document height, possibly with minor gaps due to PDF rendering artifacts.
- **A-004**: "Full-height" is defined as ≥ 70% of image height to accommodate minor gaps from PDF-to-PNG conversion.
- **A-005**: The fix is strictly scoped to the `ClassicalBorderDetector`. The SAM-based detector is explicitly out of scope and remains unchanged; any SAM detection issues are deferred to a separate feature.
