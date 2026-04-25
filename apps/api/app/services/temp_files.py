from pathlib import Path


def remove_file_if_exists(file_path: str | None) -> None:
    if file_path is None:
        return

    path = Path(file_path)
    if path.exists():
        path.unlink()
