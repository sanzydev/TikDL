from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TikTokVideoMetadata:
    id: str
    author_username: str
    author_nickname: str = ""
    title: str = ""
    description: str = ""
    duration: int = 0
    resolution: str = "Unknown"
    width: Optional[int] = None
    height: Optional[int] = None
    thumbnail_url: Optional[str] = None
    upload_date: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    share_count: Optional[int] = None

    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    audio_title: Optional[str] = None
    audio_author: Optional[str] = None
    photos: List[str] = field(default_factory=list)

    is_private: bool = False
    is_available: bool = True
    error_reason: Optional[str] = None

    @property
    def formatted_duration(self) -> str:
        if not self.duration or self.duration <= 0:
            return "00:00"
        hours = self.duration // 3600
        minutes = (self.duration % 3600) // 60
        seconds = self.duration % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def formatted_upload_date(self) -> Optional[str]:
        if not self.upload_date:
            return None
        try:
            ts = float(self.upload_date)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, TypeError, OSError):
            return self.upload_date

    def to_json_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "id": self.id,
            "author": self.author_username,
            "nickname": self.author_nickname,
            "title": self.title,
            "description": self.description,
            "duration": self.duration,
            "formatted_duration": self.formatted_duration,
            "resolution": self.resolution,
            "width": self.width,
            "height": self.height,
            "thumbnail": self.thumbnail_url,
            "upload_date": self.formatted_upload_date,
            "views": self.view_count,
            "likes": self.like_count,
            "comments": self.comment_count,
            "shares": self.share_count,
            "video_url": self.video_url,
            "audio_url": self.audio_url,
            "music": {
                "title": self.audio_title,
                "author": self.audio_author,
                "url": self.audio_url,
            } if self.audio_url else None,
            "photos": self.photos,
        }
        return data

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DownloadResult:
    url: str
    success: bool
    saved_path: Optional[Path] = None
    saved_paths: List[Path] = field(default_factory=list)
    file_size: int = 0
    metadata: Optional[TikTokVideoMetadata] = None
    error_message: Optional[str] = None
    skipped: bool = False


@dataclass
class BatchSummary:
    total: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    results: List[DownloadResult] = field(default_factory=list)

    def add_result(self, result: DownloadResult) -> None:
        self.total += 1
        self.results.append(result)
        if result.success:
            self.completed += 1
        elif result.skipped:
            self.skipped += 1
        else:
            self.failed += 1
