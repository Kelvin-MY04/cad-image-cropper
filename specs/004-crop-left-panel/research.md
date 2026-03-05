# Research: Image Detection and Cropping — Left Panel Border Crop

**Feature**: 004-crop-left-panel
**Date**: 2026-03-05

---

## 1. Detection Strategy: Contour-Based vs HoughLinesP

**Decision**: Use contour-based rectangle detection (`cv2.findContours` + `cv2.approxPolyDP`).

**Rationale**:
- `findContours` directly returns a closed polygon; no line-segment stitching needed
- After morphological opening filters out thin lines, only a few large contours remain → fast even on 12000×8000px images
- `approxPolyDP` gives 4-vertex polygon coordinates directly; bounding box is trivial
- "Widest rectangle" selection = sort by `cv2.contourArea()` descending; area already encodes both width and height

**Alternatives considered**:
- `HoughLinesP`: returns individual segments, not polygons; requires complex post-processing to cluster 4 border lines and find their intersections; more sensitive to parameter tuning
- Column/row dark-pixel counting (used in feature 003): finds vertical separator but not a full 4-sided bounding box

---

## 2. Thick vs Thin Line Isolation

**Decision**: Morphological OPEN with a 4×4 `MORPH_RECT` kernel.

**Rationale**:
- At 750 DPI: 1 px ≈ 0.034 mm; thin interior lines are 1–3 px; bold borders are ≥5 px
- A 4×4 erosion destroys lines ≤3 px (they disappear) while lines ≥5 px survive (thinned by 2 px per side, restored by dilation)
- `MORPH_OPEN` (erode + dilate with same kernel) removes thin lines and restores surviving thick structures
- Kernel 3×3 is too small: some thick 3-px lines may survive; kernel 5×5+ risks eroding narrow border corners

**Parameter**: `BORDER_OPEN_KERNEL_SIZE = 4`

---

## 3. Thresholding

**Decision**: `cv2.THRESH_BINARY + cv2.THRESH_OTSU` on the grayscale-inverted image.

**Rationale**:
- CAD floor plan scans may have varying background brightness across the page (scanner non-uniformity, PDF-to-PNG conversion artifacts)
- Otsu finds the optimal global threshold by minimising intra-class variance; consistently selects the correct threshold for bimodal white-background/black-ink histograms without manual tuning
- Fixed threshold would require per-batch calibration

---

## 4. Contour Retrieval Mode

**Decision**: `RETR_EXTERNAL` + `CHAIN_APPROX_SIMPLE`.

**Rationale**:
- `RETR_EXTERNAL` returns only outermost contours; after morphological opening removes interior thin lines, the main panel border dominates as the largest external contour
- `CHAIN_APPROX_SIMPLE` compresses horizontal/vertical runs to endpoints, significantly reducing memory and processing cost on large images

**Risk**: If the border has gaps (ink breaks, scan artefacts), `RETR_EXTERNAL` may miss it. Mitigation: the 4×4 morphological closing step tends to bridge small gaps (≤3 px).

---

## 5. Rectangle Approximation

**Decision**: `cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)`.
Accept contour if: `len(approx) == 4` and `cv2.isContourConvex(approx)`.

**Rationale**:
- `epsilon = 0.02 * arcLength` is the industry-standard starting point for rectangle detection on document scans; robust to minor ink irregularities at corners
- `0.01 * arcLength` is too tight: preserves artefacts, often giving 5–8 vertices on a nominally rectangular contour
- `0.05 * arcLength` over-simplifies and may merge adjacent edges
- `isContourConvex` eliminates L-shaped or notched regions that happen to approximate to 4 vertices

**Parameters**: `BORDER_APPROX_POLY_EPSILON = 0.02`

---

## 6. Candidate Qualification and Selection

**Decision**: Filter by width ≥ 40% and height ≥ 50% of image dimensions; select candidate with greatest width; tiebreak by smallest left-edge x.

**Rationale**:
- Direct translation of spec requirements (FR-003, Assumptions)
- Width ≥ 40% eliminates title block sub-panels and annotation boxes (which are typically <20% of image width)
- Height ≥ 50% eliminates horizontal annotation bands
- "Greatest width" is the primary discriminator between the drawing panel and inner bordered title block rows

**Constants**:
- `BORDER_MIN_WIDTH_RATIO = 0.40`
- `BORDER_MIN_HEIGHT_RATIO = 0.50`

---

## 7. DetectionResult Model Change

**Decision**: Replace `x_coordinate: int | None` with `crop_region: CropRegion | None` in `DetectionResult`.

**Rationale**:
- The new detection returns a 4-coordinate bounding box, not a single x position
- Keeping `x_coordinate` alongside `crop_region` would be a DRY violation and an ambiguous interface
- `SamBorderDetector` already has the segmentation mask and can trivially extract a bounding box (`np.where` on rows/cols of the mask); no net complexity increase
- `TwoStageDetector._is_result_sufficient`: single token change (`x_coordinate → crop_region`)
- `ImageProcessor._build_crop_region`: simplifies from constructing a `CropRegion` to returning `detection.crop_region` directly

**Alternatives considered**:
- Add `crop_region` as an additional optional field alongside `x_coordinate`: creates two parallel representations of the same concept; rejected as a DRY violation
- Keep `x_coordinate` and compute only `x_end` from border detection: loses `y_start`/`y_end` information needed to crop vertical margins; rejected

---

## Summary Table

| Decision | Choice | Key Parameter |
|---|---|---|
| Detection algorithm | `findContours` + `approxPolyDP` | RETR_EXTERNAL |
| Thick-line isolation | Morphological OPEN | kernel 4×4 |
| Thresholding | THRESH_OTSU | on inverted grayscale |
| Rectangle criterion | 4 vertices + convex | epsilon 0.02 × arcLength |
| Qualification filter | width ≥ 40%, height ≥ 50% | BORDER_MIN_WIDTH_RATIO, BORDER_MIN_HEIGHT_RATIO |
| Candidate selection | Greatest width, leftmost tiebreak | per spec FR-003 |
| DetectionResult | `crop_region: CropRegion \| None` | replaces x_coordinate |
