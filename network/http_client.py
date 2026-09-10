import os
import time
from pathlib import Path
from typing import Callable, Dict, Optional

import httpx

from config.settings import Settings, get_settings
from utils.logging import get_logger

logger = get_logger("network")


class NetworkError(Exception):
    pass


class TimeoutError(NetworkError):
    pass


class HttpError(NetworkError):
    def __init__(self, status_code: int, message: str):
        super().__init__(f"HTTP {status_code}: {message}")
        self.status_code = status_code
        self.message = message


class RateLimitError(NetworkError):
    pass


class HttpClient:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._client = httpx.Client(
            headers=self.settings.default_headers,
            timeout=self.settings.timeout,
            follow_redirects=True,
            verify=True,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        req_timeout = timeout or self.settings.timeout
        max_retries = self.settings.max_retries
        backoff = self.settings.retry_backoff

        last_exception: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"GET {url} (Attempt {attempt}/{max_retries})")
                response = self._client.get(
                    url,
                    headers=headers,
                    follow_redirects=follow_redirects,
                    timeout=req_timeout,
                )

                if response.status_code == 429:
                    logger.warning(f"Rate limited (HTTP 429) on attempt {attempt}")
                    if attempt < max_retries:
                        time.sleep(backoff * (2 ** (attempt - 1)))
                        continue
                    raise RateLimitError("Rate limit encountered from server.")

                if 500 <= response.status_code < 600:
                    logger.warning(f"Server error {response.status_code} on attempt {attempt}")
                    if attempt < max_retries:
                        time.sleep(backoff * (2 ** (attempt - 1)))
                        continue
                    raise HttpError(response.status_code, f"Server error: {response.reason_phrase}")

                if response.status_code == 404:
                    raise HttpError(404, "Requested resource was not found.")

                if response.status_code == 403:
                    raise HttpError(403, "Access forbidden or resource unavailable.")

                response.raise_for_status()
                return response

            except httpx.TimeoutException as exc:
                last_exception = exc
                logger.warning(f"Timeout on attempt {attempt}: {exc}")
                if attempt < max_retries:
                    time.sleep(backoff * (2 ** (attempt - 1)))
                    continue
                raise TimeoutError(f"Request timed out after {req_timeout}s.") from exc

            except httpx.RequestError as exc:
                last_exception = exc
                logger.warning(f"Request error on attempt {attempt}: {exc}")
                if attempt < max_retries:
                    time.sleep(backoff * (2 ** (attempt - 1)))
                    continue
                raise NetworkError(f"Network connection failed: {exc}") from exc

        raise NetworkError(f"Failed after {max_retries} attempts. Last error: {last_exception}")

    def stream_download(
        self,
        url: str,
        target_path: Path,
        headers: Optional[Dict[str, str]] = None,
        progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
    ) -> Path:
        req_headers = dict(self.settings.download_headers)
        if headers:
            req_headers.update(headers)

        part_path = target_path.with_suffix(f"{target_path.suffix}.part")
        logger.debug(f"Starting stream download from {url} to {part_path}")

        try:
            with self._client.stream("GET", url, headers=req_headers, follow_redirects=True) as response:
                if response.status_code == 429:
                    raise RateLimitError("Rate limited during download.")
                if response.status_code >= 400:
                    raise HttpError(response.status_code, f"Failed to download media stream: {response.reason_phrase}")

                total_bytes: Optional[int] = None
                content_length = response.headers.get("Content-Length")
                if content_length and content_length.isdigit():
                    total_bytes = int(content_length)

                downloaded_bytes = 0
                chunk_size = self.settings.chunk_size

                target_path.parent.mkdir(parents=True, exist_ok=True)

                with open(part_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded_bytes += len(chunk)
                            if progress_callback:
                                progress_callback(downloaded_bytes, total_bytes)

            if os.path.exists(target_path):
                target_path.unlink()
            part_path.replace(target_path)
            logger.debug(f"Download completed successfully: {target_path} ({downloaded_bytes} bytes)")
            return target_path

        except Exception as exc:
            if part_path.exists():
                try:
                    part_path.unlink()
                except Exception:
                    pass
            logger.error(f"Download failed: {exc}")
            raise
