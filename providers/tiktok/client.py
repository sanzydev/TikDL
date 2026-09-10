from typing import Optional

from config.settings import Settings, get_settings
from network.http_client import HttpClient, HttpError, NetworkError, TimeoutError
from providers.tiktok.models import TikTokVideoMetadata
from providers.tiktok.parser import TikTokParser, TikTokParsingError, VideoUnavailableError
from utils.logging import get_logger
from utils.urls import (
    extract_video_id_from_url,
    is_valid_tiktok_url,
    normalize_tiktok_url,
)

logger = get_logger("provider.tiktok")


class TikTokClient:
    def __init__(self, http_client: Optional[HttpClient] = None, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.http = http_client or HttpClient(self.settings)

    def close(self) -> None:
        self.http.close()

    def __enter__(self) -> "TikTokClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def fetch_metadata(self, url: str) -> TikTokVideoMetadata:
        if not is_valid_tiktok_url(url):
            raise ValueError(f"Invalid or unsupported TikTok URL: {url}")

        clean_url = normalize_tiktok_url(url)
        logger.debug(f"Fetching metadata for: {clean_url}")

        expected_id = extract_video_id_from_url(clean_url)

        if not expected_id:
            try:
                head_resp = self.http.get(clean_url)
                final_url = str(head_resp.url)
                expected_id = extract_video_id_from_url(final_url)
            except Exception as exc:
                logger.debug(f"Could not resolve redirect: {exc}")

        if expected_id:
            embed_url = f"https://www.tiktok.com/embed/v2/{expected_id}"
            try:
                logger.debug(f"Attempting embed fetch: {embed_url}")
                embed_resp = self.http.get(embed_url)
                if embed_resp.status_code == 200 and "__FRONTITY_CONNECT_STATE__" in embed_resp.text:
                    return TikTokParser.parse_html(embed_resp.text, expected_id=expected_id)
            except Exception as exc:
                logger.debug(f"Embed fetch fallback: {exc}")

        try:
            response = self.http.get(clean_url)
            final_url = str(response.url)
            if not expected_id:
                expected_id = extract_video_id_from_url(final_url)

            html = response.text
            if ("SlardarWAF" in html or "verify-center" in html) and expected_id:
                embed_url = f"https://www.tiktok.com/embed/v2/{expected_id}"
                embed_resp = self.http.get(embed_url)
                if embed_resp.status_code == 200:
                    return TikTokParser.parse_html(embed_resp.text, expected_id=expected_id)

            metadata = TikTokParser.parse_html(html, expected_id=expected_id)
            return metadata

        except (VideoUnavailableError, TikTokParsingError):
            raise
        except HttpError as exc:
            if exc.status_code == 404:
                raise VideoUnavailableError("The video is private, deleted, or was not found.") from exc
            if exc.status_code == 403:
                raise VideoUnavailableError("The video is private or restricted by access controls.") from exc
            raise VideoUnavailableError(f"HTTP error {exc.status_code} accessing video.") from exc
        except TimeoutError as exc:
            raise NetworkError(f"Connection timed out while fetching video info: {exc}") from exc
        except NetworkError:
            raise
        except Exception as exc:
            logger.error(f"Unexpected error fetching metadata: {exc}")
            raise TikTokParsingError(f"Unable to fetch video: {exc}") from exc
