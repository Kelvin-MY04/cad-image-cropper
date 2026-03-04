from enum import Enum


class ProcessingStatus(Enum):
    SUCCESS = "SUCCESS"
    SKIPPED_NO_BORDER = "SKIPPED_NO_BORDER"
    SKIPPED_CORRUPT = "SKIPPED_CORRUPT"
    FAILED = "FAILED"
