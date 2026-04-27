from enum import StrEnum


class JobStatus(StrEnum):
    UPLOADED = "uploaded"
    # Reserved for a future explicit validation phase.
    VALIDATING = "validating"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
