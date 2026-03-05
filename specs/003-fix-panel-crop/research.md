# Research: Fix Panel Detection and Cropping

**Branch**: `003-fix-panel-crop` | **Date**: 2026-03-05

## Root Cause Analysis

### Decision: Selection strategy is the primary failure point

The current `ClassicalBorderDetector._cluster_and_select_dominant_x` selects the x-position with the **most detected vertical lines** across the entire image. In a dense CAD floor plan with hundreds of wall segments, grid lines, and dimension tick marks, the most common vertical x-position is always an interior drawing element — not the title block separator.

**Rationale**: The separator may generate only 1–3 Hough line detections (one long continuous segment), while interior walls and dimension lines generate dozens of overlapping short segments at repeated x-positions, dominating the vote count.

**Alternatives considered**:
- Increasing `HOUGH_MIN_LINE_LENGTH_RATIO` to filter out shorter segments — rejected as sole fix because the separator may appear as multiple fragmented segments that individually fail the length threshold but collectively span the full height.
- Using horizontal projection profiles instead of Hough — rejected as it abandons the existing well-structured algorithm and requires more validation.

---

## Decision: Algorithm fix — spatial + height filtering, not vote counting

**Decision**: Replace the "most votes" selection with:
1. Aggregate detected vertical segments by x-bin (same bin-width = 10px)
2. Per bin, compute the **union of y-spans** covered by all segments in that bin
3. Filter bins to those whose y-coverage ≥ 70% of image height (`SEPARATOR_MIN_HEIGHT_RATIO`)
4. Among qualifying bins, search only the **right zone** (70–95% of image width)
5. Return the **leftmost** qualifying x in that zone (the drawing-to-title-block boundary)

**Rationale**:
- A full-height separator that appears as two fragments (top 40%, bottom 35%) still sums to 75% y-coverage and passes the filter — robust to PDF rendering gaps.
- Interior wall lines, even if numerous at the same x, have combined y-span of 20–40% and are rejected by the height filter.
- The right zone constraint (70–95% of width) excludes the drawing's own outer border lines and dimension lines inside the floor plan.
- "Leftmost in zone" correctly picks the drawing-boundary line even when the title block has internal dividers.

**Alternatives considered**:
- "Rightmost in zone" — rejected because it would select a line inside the title block, not the boundary.
- "Densest cluster in zone" — rejected for the same reason as the original: interior lines inside the title block zone could still dominate.

---

## Decision: Existing test stripe placement must shift into right zone

**Decision**: Update synthetic test image stripe from `stripe_x=600` (50% of 1200px) to `stripe_x=900` (75% of 1200px) in both unit and integration tests.

**Rationale**: After the fix, the detector only searches in the right zone (70–95% of width = 840–1140px for a 1200px image). A stripe at x=600 is outside this zone and correctly returns `DetectionMethod.NONE`. Tests validating correct detection must position the separator where real separators appear.

**Alternatives considered**:
- Adding a fallback to search the full image when right zone yields no result — rejected as this reintroduces the original failure mode.

---

## Decision: New constants for zone boundaries and height threshold

**Decision**: Add three named constants to `constants.py`:
- `SEPARATOR_MIN_HEIGHT_RATIO: float = 0.70` — minimum y-coverage ratio for a line cluster to qualify as a separator
- `TITLE_BLOCK_ZONE_LEFT_RATIO: float = 0.70` — left boundary of title block search zone (% of width)
- `TITLE_BLOCK_ZONE_RIGHT_RATIO: float = 0.95` — right boundary of title block search zone (% of width)

**Rationale**: Magic numbers violate Principle IV (Clean Code). These values need to be tunable as constants, not inline literals. The 5% right-side exclusion prevents detecting the document's outermost right border as the separator.

---

## Decision: No contracts/ directory needed

**Decision**: Skip Phase 1 contracts artifact.

**Rationale**: The CLI command signature (`cad-crop`) does not change. The `BorderDetector.detect_border` public method signature does not change. Only private method internals within `ClassicalBorderDetector` are modified — these are not external contracts.
