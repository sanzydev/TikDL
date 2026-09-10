import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

__version__ = "1.0.0"
__app_name__ = "TikDL"


@dataclass
class Settings:
    app_name: str = "TikDL"
    version: str = "1.0.0"

    output_dir: Path = field(default_factory=lambda: Path(
        os.getenv("TIKTDL_OUTPUT_DIR") or os.getenv("TIKDL_OUTPUT_DIR") or "downloads"
    ))
    timeout: float = field(default_factory=lambda: float(os.getenv("TIKDL_TIMEOUT", "15.0")))
    max_retries: int = field(default_factory=lambda: int(os.getenv("TIKDL_RETRIES", "3")))
    retry_backoff: float = 1.0
    chunk_size: int = 65536
    debug: bool = field(default_factory=lambda: os.getenv("TIKDL_DEBUG", "0").lower() in ("1", "true", "yes"))

    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    )

    default_headers: Dict[str, str] = field(default_factory=lambda: {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/130.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Ch-Ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    })

    download_headers: Dict[str, str] = field(default_factory=lambda: {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/130.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.tiktok.com/",
        "Accept": "*/*",
        "Accept-Encoding": "identity;q=1, *;q=0",
        "Range": "bytes=0-",
    })


def get_settings() -> Settings:
    return Settings()
