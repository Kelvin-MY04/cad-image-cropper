import os
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt
import torch

from cad_image_cropper.constants import SAM_CONFIDENCE_THRESHOLD, SAM_MODEL_ID
from cad_image_cropper.detectors.border_detector import BorderDetector
from cad_image_cropper.exceptions import BorderDetectionError, ModelLoadError
from cad_image_cropper.models.detection_method import DetectionMethod
from cad_image_cropper.models.detection_result import DetectionResult
from cad_image_cropper.models.image_metadata import ImageMetadata


class SamBorderDetector(BorderDetector):
    def __init__(self) -> None:
        try:
            from transformers import SamModel, SamProcessor

            token = os.environ.get("HF_TOKEN")
            self._processor: object = SamProcessor.from_pretrained(SAM_MODEL_ID, token=token)
            self._model: object = SamModel.from_pretrained(SAM_MODEL_ID, token=token)
        except Exception as exc:
            raise ModelLoadError(
                f"Failed to load SAM model '{SAM_MODEL_ID}': {exc}",
                Path(SAM_MODEL_ID),
            ) from exc

    def detect_border(
        self, metadata: ImageMetadata, image_array: npt.NDArray[Any]
    ) -> DetectionResult:
        try:
            approx_x = self._estimate_x_by_column_darkness(image_array, metadata.width)
            inputs = self._processor(  # type: ignore[operator]
                images=image_array,
                input_points=[[[approx_x, metadata.height // 2]]],
                return_tensors="pt",
            )
            with torch.no_grad():
                outputs = self._model(**inputs)  # type: ignore[operator]
            masks = self._processor.image_processor.post_process_masks(  # type: ignore[attr-defined]
                outputs.pred_masks,
                inputs["original_sizes"],
                inputs["reshaped_input_sizes"],
            )
            scores = outputs.iou_scores[0][0].tolist()
            best_idx = int(torch.argmax(outputs.iou_scores[0][0]).item())
            best_score = float(scores[best_idx])
            if not self._is_high_confidence(best_score):
                return DetectionResult(
                    x_coordinate=None,
                    confidence=best_score,
                    method=DetectionMethod.NONE,
                )
            mask = masks[0][0][best_idx].numpy()
            x = self._extract_x_from_mask(mask)
            if x is None:
                return DetectionResult(
                    x_coordinate=None,
                    confidence=best_score,
                    method=DetectionMethod.NONE,
                )
            return DetectionResult(
                x_coordinate=x,
                confidence=best_score,
                method=DetectionMethod.MODEL_SAM,
            )
        except Exception as exc:
            raise BorderDetectionError(
                f"SAM detection failed: {exc}", metadata.file_path
            ) from exc

    def _estimate_x_by_column_darkness(
        self, image_array: npt.NDArray[Any], width: int
    ) -> int:
        if len(image_array.shape) == 3:
            gray = np.mean(image_array, axis=2)
        else:
            gray = image_array.astype(float)
        col_means = gray.mean(axis=0)
        edge_margin = int(width * 0.05)
        col_means[:edge_margin] = float("inf")
        col_means[width - edge_margin :] = float("inf")
        return int(np.argmin(col_means))

    def _extract_x_from_mask(
        self, mask: npt.NDArray[Any]
    ) -> int | None:
        col_sums = mask.sum(axis=0)
        nonzero = np.nonzero(col_sums)[0]
        if len(nonzero) == 0:
            return None
        return int(nonzero[0])

    def _is_high_confidence(self, score: float) -> bool:
        return score >= SAM_CONFIDENCE_THRESHOLD
