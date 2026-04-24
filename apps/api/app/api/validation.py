ALLOWED_UPLOAD_CONTENT_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/webm",
}
MAX_UPLOAD_FILE_SIZE_BYTES = 100 * 1024 * 1024
UPLOAD_OBJECT_KEY_PREFIX = "uploads/"


def normalize_non_empty_text(value: str, field_name: str) -> str:
    normalized = value.strip()

    if not normalized:
        raise ValueError(f"{field_name} must not be empty")

    return normalized


def validate_filename_like(value: str, field_name: str) -> str:
    normalized = normalize_non_empty_text(value, field_name)

    if "/" in normalized or "\\" in normalized:
        raise ValueError(f"{field_name} must not contain path separators")

    return normalized


def validate_upload_content_type(value: str) -> str:
    normalized = normalize_non_empty_text(value, "content_type").lower()

    if normalized not in ALLOWED_UPLOAD_CONTENT_TYPES:
        raise ValueError("unsupported content_type")

    return normalized


def validate_upload_file_size(value: int) -> int:
    if value <= 0:
        raise ValueError("file_size must be greater than 0")

    if value > MAX_UPLOAD_FILE_SIZE_BYTES:
        raise ValueError("file_size exceeds the maximum allowed size")

    return value


def validate_upload_object_key(value: str) -> str:
    normalized = normalize_non_empty_text(value, "input_object_key")

    if not normalized.startswith(UPLOAD_OBJECT_KEY_PREFIX):
        raise ValueError(f"input_object_key must start with {UPLOAD_OBJECT_KEY_PREFIX}")

    return normalized
