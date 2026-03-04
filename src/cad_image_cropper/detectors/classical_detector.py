from typing import Any

import cv2
import numpy as np
import numpy.typing as npt

from cad_image_cropper.constants import (
    HOUGH_ANGLE_TOLERANCE_PX,
    HOUGH_MAX_LINE_GAP,
    HOUGH_MIN_LINE_LENGTH_RATIO,
    HOUGH_THRESHOLD,
)
from cad_image_cropper.detectors.border_detector import BorderDetector
from cad_image_cropper.exceptions import BorderDetectionError
from cad_image_cropper.models.detection_method import DetectionMethod
from cad_image_cropper.models.detection_result import DetectionResult
from cad_image_cropper.models.image_metadata import ImageMetadata


class ClassicalBorderDetector(BorderDetector):
    def detect_border(
        self, metadata: ImageMetadata, image_array: npt.NDArray[Any]
    ) -> DetectionResult:
        try:
            gray = self._convert_to_grayscale_array(image_array)
            morphed = self._apply_vertical_morphology(gray, metadata.height)
            thresholded = self._apply_binary_threshold(morphed)
            lines = self._run_hough_lines(thresholded, metadata.height)
            if lines is None:
                return DetectionResult(
                    x_coordinate=None,
                    confidence=None,
                    method=DetectionMethod.NONE,
                )
            vertical = self._filter_vertical_lines(lines)
            if not vertical:
                return DetectionResult(
                    x_coordinate=None,
                    confidence=None,
                    method=DetectionMethod.NONE,
                )
            x = self._cluster_and_select_dominant_x(vertical, metadata.width)
            if x is None:
                return DetectionResult(
                    x_coordinate=None,
                    confidence=None,
                    method=DetectionMethod.NONE,
                )
            return DetectionResult(
                x_coordinate=x,
                confidence=None,
                method=DetectionMethod.CLASSICAL,
            )
        except (cv2.error, ValueError, IndexError) as exc:
            raise BorderDetectionError(
                f"Classical detection failed: {exc}", metadata.file_path
            ) from exc

    def _convert_to_grayscale_array(
        self, image_array: npt.NDArray[Any]
    ) -> npt.NDArray[Any]:
        if len(image_array.shape) == 2:
            gray = image_array
        else:
            gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        return cv2.bitwise_not(gray)

    def _apply_vertical_morphology(
        self, gray: npt.NDArray[Any], height: int
    ) -> npt.NDArray[Any]:
        kernel_height = max(50, height // 20)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_height))
        return cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)

    def _apply_binary_threshold(
        self, morphed: npt.NDArray[Any]
    ) -> npt.NDArray[Any]:
        _, thresholded = cv2.threshold(morphed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresholded

    def _run_hough_lines(
        self, thresholded: npt.NDArray[Any], height: int
    ) -> npt.NDArray[Any] | None:
        min_length = int(height * HOUGH_MIN_LINE_LENGTH_RATIO)
        return cv2.HoughLinesP(
            thresholded,
            rho=1,
            theta=float(np.pi / 180),
            threshold=HOUGH_THRESHOLD,
            minLineLength=min_length,
            maxLineGap=HOUGH_MAX_LINE_GAP,
        )

    def _filter_vertical_lines(
        self, lines: npt.NDArray[Any]
    ) -> list[int]:
        result: list[int] = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(x2 - x1) <= HOUGH_ANGLE_TOLERANCE_PX:
                result.append((x1 + x2) // 2)
        return result

    def _cluster_and_select_dominant_x(
        self, x_values: list[int], image_width: int
    ) -> int | None:
        bin_width = 10
        edge_margin = int(image_width * 0.05)
        bins: dict[int, list[int]] = {}
        for x in x_values:
            if x < edge_margin or x > image_width - edge_margin:
                continue
            bin_key = x // bin_width
            bins.setdefault(bin_key, []).append(x)
        if not bins:
            return None
        dominant_bin = max(bins, key=lambda k: len(bins[k]))
        return int(np.mean(bins[dominant_bin]))
