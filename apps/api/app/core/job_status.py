from enum import StrEnum


class JobStatus(StrEnum):
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
