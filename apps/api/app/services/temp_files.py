from pathlib import Path


def remove_file_if_exists(file_path: str | None) -> None:
    if file_path is None:
        return

    try:
        Path(file_path).unlink(missing_ok=True)
    except OSError as error:
        print(f"Failed to remove temporary file {file_path}: {error}")
