import time
from pathlib import Path
from typing import Optional

from providers.tiktok.models import TikTokVideoMetadata
from utils.files import ensure_directory, ensure_unique_path, sanitize_filename


def generate_download_filename(
    metadata: TikTokVideoMetadata,
    is_audio: bool = False,
    timestamp: Optional[int] = None,
) -> str:
    extension = ".mp3" if is_audio else ".mp4"
    ts = timestamp or int(time.time())

    author = metadata.author_username.strip() if metadata.author_username else ""
    video_id = metadata.id.strip() if metadata.id else ""

    if author and video_id:
        raw_name = f"{author}_{video_id}{extension}"
    elif video_id:
        raw_name = f"video_{video_id}{extension}"
    else:
        raw_name = f"video_{ts}{extension}"

    return sanitize_filename(raw_name, fallback=f"video_{ts}{extension}")


def generate_download_path(
    metadata: TikTokVideoMetadata,
    output_dir: Path,
    is_audio: bool = False,
    avoid_overwrite: bool = True,
) -> Path:
    ensure_directory(output_dir)
    filename = generate_download_filename(metadata, is_audio=is_audio)
    target_path = output_dir / filename

    if avoid_overwrite:
        return ensure_unique_path(target_path)
    return target_path
