from pathlib import Path
from typing import Callable, Iterable, List, Optional

from config.settings import Settings, get_settings
from core.filename import generate_download_path
from network.http_client import HttpClient, HttpError, NetworkError, RateLimitError, TimeoutError
from providers.tiktok.client import TikTokClient
from providers.tiktok.models import BatchSummary, DownloadResult, TikTokVideoMetadata
from providers.tiktok.parser import TikTokParsingError, VideoUnavailableError
from utils.logging import get_logger
from utils.urls import is_valid_tiktok_url

logger = get_logger("downloader")


class Downloader:
    def __init__(
        self,
        settings: Optional[Settings] = None,
        client: Optional[TikTokClient] = None,
        http_client: Optional[HttpClient] = None,
    ):
        self.settings = settings or get_settings()
        self.http = http_client or HttpClient(self.settings)
        self.client = client or TikTokClient(self.http, self.settings)

    def close(self) -> None:
        self.client.close()
        self.http.close()

    def __enter__(self) -> "Downloader":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def fetch_info(self, url: str) -> TikTokVideoMetadata:
        if not is_valid_tiktok_url(url):
            raise ValueError("Invalid TikTok URL provided.")
        return self.client.fetch_metadata(url)

    def download_single(
        self,
        url: str,
        output_dir: Optional[Path] = None,
        is_audio: bool = False,
        progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
        on_metadata: Optional[Callable[[TikTokVideoMetadata], None]] = None,
    ) -> DownloadResult:
        out_dir = output_dir or self.settings.output_dir

        if not is_valid_tiktok_url(url):
            return DownloadResult(
                url=url,
                success=False,
                error_message="Invalid TikTok URL. Please check the URL format.",
            )

        try:
            logger.debug(f"Fetching metadata for download: {url}")
            metadata = self.client.fetch_metadata(url)

            if on_metadata:
                on_metadata(metadata)

            media_url = metadata.audio_url if is_audio else metadata.video_url

            if not media_url:
                if not is_audio and metadata.photos:
                    return self._download_photos(metadata, out_dir, progress_callback)

                media_type = "audio" if is_audio else "video"
                return DownloadResult(
                    url=url,
                    success=False,
                    metadata=metadata,
                    error_message=f"No public {media_type} stream URL available for this post.",
                )

            target_path = generate_download_path(
                metadata=metadata,
                output_dir=out_dir,
                is_audio=is_audio,
                avoid_overwrite=True,
            )

            logger.debug(f"Saving to destination: {target_path}")

            saved_path = self.http.stream_download(
                url=media_url,
                target_path=target_path,
                progress_callback=progress_callback,
            )

            file_size = saved_path.stat().st_size if saved_path.exists() else 0

            return DownloadResult(
                url=url,
                success=True,
                saved_path=saved_path,
                saved_paths=[saved_path],
                file_size=file_size,
                metadata=metadata,
            )

        except VideoUnavailableError as exc:
            return DownloadResult(
                url=url,
                success=False,
                error_message=str(exc) or "The video is private or unavailable.",
            )
        except TikTokParsingError as exc:
            return DownloadResult(
                url=url,
                success=False,
                error_message=str(exc) or "Unable to extract public video metadata.",
            )
        except RateLimitError as exc:
            return DownloadResult(
                url=url,
                success=False,
                error_message=str(exc) or "Rate limit exceeded. Please try again later.",
            )
        except TimeoutError as exc:
            return DownloadResult(
                url=url,
                success=False,
                error_message=f"Network request timed out: {exc}",
            )
        except (HttpError, NetworkError) as exc:
            return DownloadResult(
                url=url,
                success=False,
                error_message=f"Network error: {exc}",
            )
        except Exception as exc:
            logger.error(f"Unexpected error in download_single: {exc}")
            return DownloadResult(
                url=url,
                success=False,
                error_message=f"Unexpected error: {exc}",
            )

    def download_multiple(
        self,
        urls: Iterable[str],
        output_dir: Optional[Path] = None,
        is_audio: bool = False,
        on_start: Optional[Callable[[int, int, str], None]] = None,
        on_progress: Optional[Callable[[int, Optional[int]], None]] = None,
        on_complete: Optional[Callable[[int, int, DownloadResult], None]] = None,
    ) -> BatchSummary:
        url_list = [u.strip() for u in urls if u and u.strip()]
        total = len(url_list)
        summary = BatchSummary()

        for index, url in enumerate(url_list, start=1):
            if on_start:
                on_start(index, total, url)

            result = self.download_single(
                url=url,
                output_dir=output_dir,
                is_audio=is_audio,
                progress_callback=on_progress,
            )

            summary.add_result(result)

            if on_complete:
                on_complete(index, total, result)

        return summary

    def _download_photos(
        self,
        metadata: TikTokVideoMetadata,
        output_dir: Path,
        progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
    ) -> DownloadResult:
        from utils.files import ensure_directory, ensure_unique_path, sanitize_filename

        ensure_directory(output_dir)
        saved_paths: List[Path] = []
        total_bytes = 0
        total_photos = len(metadata.photos)
        author = metadata.author_username or "user"
        video_id = metadata.id or "photo"

        for idx, photo_url in enumerate(metadata.photos, start=1):
            if total_photos == 1:
                filename = sanitize_filename(f"{author}_{video_id}.jpg", fallback=f"photo_{video_id}.jpg")
            else:
                filename = sanitize_filename(f"{author}_{video_id}_{idx}.jpg", fallback=f"photo_{video_id}_{idx}.jpg")
            target_path = ensure_unique_path(output_dir / filename)
            saved = self.http.stream_download(photo_url, target_path)
            saved_paths.append(saved)
            size = saved.stat().st_size if saved.exists() else 0
            total_bytes += size
            if progress_callback:
                progress_callback(idx, total_photos)

        return DownloadResult(
            url=f"https://www.tiktok.com/@{author}/photo/{video_id}",
            success=True,
            saved_path=saved_paths[0] if saved_paths else None,
            saved_paths=saved_paths,
            file_size=total_bytes,
            metadata=metadata,
        )
