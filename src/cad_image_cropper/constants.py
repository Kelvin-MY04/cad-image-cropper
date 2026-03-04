from pathlib import Path

DEFAULT_INPUT_DIR: Path = Path("import")
DEFAULT_OUTPUT_DIR: Path = Path("export")
SAM_MODEL_ID: str = "facebook/sam-vit-base"
SAM_CONFIDENCE_THRESHOLD: float = 0.75
HOUGH_THRESHOLD: int = 100
HOUGH_MIN_LINE_LENGTH_RATIO: float = 0.5
HOUGH_MAX_LINE_GAP: int = 20
HOUGH_ANGLE_TOLERANCE_PX: int = 5
