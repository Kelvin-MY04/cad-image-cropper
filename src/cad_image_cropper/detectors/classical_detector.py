from typing import Any

import cv2
import numpy.typing as npt

from cad_image_cropper.constants import (
    BORDER_APPROX_POLY_EPSILON,
    BORDER_MIN_HEIGHT_RATIO,
    BORDER_MIN_WIDTH_RATIO,
    BORDER_OPEN_KERNEL_SIZE,
    SEPARATOR_MIN_HEIGHT_RATIO,
    SEPARATOR_MIN_HEIGHT_RATIO_COLOR,
    TITLE_BLOCK_ZONE_INNER_LEFT_RATIO,
    TITLE_BLOCK_ZONE_LEFT_RATIO,
    TITLE_BLOCK_ZONE_RIGHT_RATIO,
)
from cad_image_cropper.detectors.border_detector import BorderDetector
from cad_image_cropper.exceptions import BorderDetectionError
from cad_image_cropper.models.crop_region import CropRegion
from cad_image_cropper.models.detection_method import DetectionMethod
from cad_image_cropper.models.detection_result import DetectionResult
from cad_image_cropper.models.image_metadata import ImageMetadata


class ClassicalBorderDetector(BorderDetector):
    def detect_border(
        self, metadata: ImageMetadata, image_array: npt.NDArray[Any]
    ) -> DetectionResult:
        try:
            gray = self._invert_grayscale(self._to_grayscale_array(image_array))
            binary = self._isolate_bold_lines(gray)
            candidates = self._find_panel_contours(binary, metadata.width, metadata.height)
            if not candidates:
                return self._no_detection()
            panel = self._select_widest_panel(candidates)
            if panel is None:
                return self._no_detection()
            x, y, w, h = panel
            separator_x = self._find_separator_x(gray, y, y + h, metadata.width)
            x_end = separator_x if separator_x is not None else x + w
            return DetectionResult(
                crop_region=CropRegion(x_start=x, x_end=x_end, y_start=y, y_end=y + h),
                confidence=None,
                method=DetectionMethod.CLASSICAL,
            )
        except (cv2.error, ValueError, IndexError) as exc:
            raise BorderDetectionError(
                f"Classical detection failed: {exc}", metadata.file_path
            ) from exc

    def _no_detection(self) -> DetectionResult:
        return DetectionResult(crop_region=None, confidence=None, method=DetectionMethod.NONE)

    def _to_grayscale_array(
        self, image_array: npt.NDArray[Any]
    ) -> npt.NDArray[Any]:
        if len(image_array.shape) == 2:
            return image_array
        return cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)

    def _invert_grayscale(
        self, gray: npt.NDArray[Any]
    ) -> npt.NDArray[Any]:
        return cv2.bitwise_not(gray)

    def _apply_binary_threshold(
        self, morphed: npt.NDArray[Any]
    ) -> npt.NDArray[Any]:
        _, thresholded = cv2.threshold(morphed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresholded

    def _isolate_bold_lines(self, gray: npt.NDArray[Any]) -> npt.NDArray[Any]:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (BORDER_OPEN_KERNEL_SIZE, BORDER_OPEN_KERNEL_SIZE)
        )
        morphed = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
        return self._apply_binary_threshold(morphed)

    def _is_qualifying_rectangle(
        self,
        approx: npt.NDArray[Any],
        x: int,
        y: int,
        w: int,
        h: int,
        img_w: int,
        img_h: int,
    ) -> bool:
        if len(approx) != 4:
            return False
        if not cv2.isContourConvex(approx):
            return False
        if w < img_w * BORDER_MIN_WIDTH_RATIO:
            return False
        return h >= img_h * BORDER_MIN_HEIGHT_RATIO

    def _find_panel_contours(
        self,
        binary: npt.NDArray[Any],
        img_w: int,
        img_h: int,
    ) -> list[tuple[int, int, int, int]]:
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates: list[tuple[int, int, int, int]] = []
        for contour in contours:
            epsilon = BORDER_APPROX_POLY_EPSILON * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)
            x, y, w, h = cv2.boundingRect(contour)
            if self._is_qualifying_rectangle(approx, x, y, w, h, img_w, img_h):
                candidates.append((x, y, w, h))
        return candidates

    def _select_widest_panel(
        self, candidates: list[tuple[int, int, int, int]]
    ) -> tuple[int, int, int, int] | None:
        if not candidates:
            return None
        return sorted(candidates, key=lambda c: (-c[2], c[0]))[0]

    def _find_separator_x(
        self, gray: npt.NDArray[Any], y_start: int, y_end: int, img_w: int
    ) -> int | None:
        region = gray[y_start:y_end, :]
        region_h = y_end - y_start
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (1, max(50, region_h // 20))
        )
        morphed = cv2.morphologyEx(region, cv2.MORPH_OPEN, kernel)
        col_sums = morphed.sum(axis=0).astype(float)
        coverage = col_sums / (255.0 * region_h)
        inner_left = int(img_w * TITLE_BLOCK_ZONE_INNER_LEFT_RATIO)
        right = int(img_w * TITLE_BLOCK_ZONE_RIGHT_RATIO)
        result = self._qualifying_columns(
            coverage, inner_left, right, SEPARATOR_MIN_HEIGHT_RATIO
        )
        if result is not None:
            return result
        result = self._qualifying_columns(
            coverage, inner_left, right, SEPARATOR_MIN_HEIGHT_RATIO_COLOR
        )
        if result is not None:
            return result
        left = int(img_w * TITLE_BLOCK_ZONE_LEFT_RATIO)
        return self._qualifying_columns(
            coverage, left, right, SEPARATOR_MIN_HEIGHT_RATIO
        )

    def _qualifying_columns(
        self,
        coverage: npt.NDArray[Any],
        left: int,
        right: int,
        threshold: float,
    ) -> int | None:
        columns = [
            x for x in range(left, right) if coverage[x] >= threshold
        ]
        return min(columns) if columns else None

