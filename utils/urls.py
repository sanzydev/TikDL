import re
from typing import Optional
from urllib.parse import urlparse, urlunparse

ALLOWED_TIKTOK_DOMAINS = {
    "tiktok.com",
    "www.tiktok.com",
    "m.tiktok.com",
    "vm.tiktok.com",
    "vt.tiktok.com",
    "t.tiktok.com",
    "lite.tiktok.com",
}

TRACKING_PARAMS = {
    "is_from_webapp",
    "sender_device",
    "sender_web_id",
    "share_item_id",
    "share_link_id",
    "share_app_id",
    "timestamp",
    "user_id",
    "sec_user_id",
    "ug_btm",
    "utm_source",
    "utm_campaign",
    "utm_medium",
    "_r",
    "_t",
    "mid",
}

VIDEO_ID_PATTERN = re.compile(r"/(?:video|v|photo)/(\d{15,22})")
AUTHOR_PATTERN = re.compile(r"/@([A-Za-z0-9_.-]+)")
SHORT_URL_PATTERN = re.compile(r"^(?:vm|vt|t)\.tiktok\.com/([A-Za-z0-9_-]+)")


def is_valid_tiktok_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False

    url_str = url.strip()
    if not url_str:
        return False

    try:
        parsed = urlparse(url_str)
    except Exception:
        return False

    if parsed.scheme not in ("http", "https"):
        return False

    netloc = parsed.netloc.lower()
    if ":" in netloc:
        netloc = netloc.split(":", 1)[0]

    is_allowed = any(
        netloc == domain or netloc.endswith("." + domain)
        for domain in ALLOWED_TIKTOK_DOMAINS
    )
    if not is_allowed:
        return False

    path = parsed.path
    if not path or path == "/":
        return False

    if is_short_tiktok_url(url_str):
        return True

    if VIDEO_ID_PATTERN.search(path):
        return True

    if path.startswith("/@") or "/video/" in path or "/v/" in path or "/photo/" in path:
        return True

    return False


def is_short_tiktok_url(url: str) -> bool:
    if not url:
        return False
    try:
        parsed = urlparse(url.strip())
        netloc = parsed.netloc.lower().split(":", 1)[0]
        if netloc in ("vm.tiktok.com", "vt.tiktok.com", "t.tiktok.com"):
            return len(parsed.path.strip("/")) > 0
        if "tiktok.com" in netloc and parsed.path.startswith("/t/"):
            return True
        return False
    except Exception:
        return False


def extract_video_id_from_url(url: str) -> Optional[str]:
    if not url:
        return None
    try:
        parsed = urlparse(url.strip())
        match = VIDEO_ID_PATTERN.search(parsed.path)
        if match:
            return match.group(1)
        return None
    except Exception:
        return None


def extract_author_from_url(url: str) -> Optional[str]:
    if not url:
        return None
    try:
        parsed = urlparse(url.strip())
        match = AUTHOR_PATTERN.search(parsed.path)
        if match:
            return match.group(1)
        return None
    except Exception:
        return None


def normalize_tiktok_url(url: str) -> str:
    if not url:
        return ""

    url_str = url.strip()
    try:
        parsed = urlparse(url_str)
        scheme = "https"
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip("/")
        if not path:
            path = "/"

        if VIDEO_ID_PATTERN.search(path):
            return urlunparse((scheme, netloc, path, "", "", ""))

        query_parts = []
        if parsed.query:
            for item in parsed.query.split("&"):
                if "=" in item:
                    k, v = item.split("=", 1)
                    if k.lower() not in TRACKING_PARAMS:
                        query_parts.append(f"{k}={v}")
                else:
                    if item.lower() not in TRACKING_PARAMS:
                        query_parts.append(item)

        clean_query = "&".join(query_parts)
        return urlunparse((scheme, netloc, path, "", clean_query, ""))
    except Exception:
        return url_str
