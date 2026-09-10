import os
import re
from pathlib import Path
from typing import Set

INVALID_CHARS_PATTERN = re.compile(r'[\<\>:"/\\\|\?\*\x00-\x1f]')

RESERVED_NAMES: Set[str] = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}

MAX_FILENAME_LENGTH = 180


def sanitize_filename(filename: str, fallback: str = "video") -> str:
    if not filename:
        return fallback

    clean_name = os.path.basename(filename.strip())
    clean_name = INVALID_CHARS_PATTERN.sub("_", clean_name)
    clean_name = re.sub(r"[\s_]+", "_", clean_name)
    clean_name = clean_name.strip(" ._")

    if not clean_name:
        clean_name = fallback

    base_upper = clean_name.split(".")[0].upper()
    if base_upper in RESERVED_NAMES:
        clean_name = f"_{clean_name}"

    if len(clean_name) > MAX_FILENAME_LENGTH:
        parts = clean_name.rsplit(".", 1)
        if len(parts) == 2:
            base, ext = parts
            clean_name = f"{base[:MAX_FILENAME_LENGTH - len(ext) - 1]}.{ext}"
        else:
            clean_name = clean_name[:MAX_FILENAME_LENGTH]

    return clean_name


def ensure_directory(directory_path: Path) -> Path:
    resolved = directory_path.resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def ensure_unique_path(target_path: Path) -> Path:
    if not target_path.exists():
        return target_path

    directory = target_path.parent
    stem = target_path.stem
    suffix = target_path.suffix

    counter = 1
    while True:
        new_path = directory / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1
