import pytest
from utils.urls import (
    extract_author_from_url,
    extract_video_id_from_url,
    is_short_tiktok_url,
    is_valid_tiktok_url,
    normalize_tiktok_url,
)


class TestTikTokUrlValidation:
    @pytest.mark.parametrize(
        "url",
        [
            "https://www.tiktok.com/@username/video/7683885896365624596",
            "http://www.tiktok.com/@username/video/7683885896365624596",
            "https://tiktok.com/@user/video/7683885896365624596",
            "https://m.tiktok.com/v/7683885896365624596.html",
            "https://vm.tiktok.com/ZMxxxxxx/",
            "https://vt.tiktok.com/ZSxxxxxx/",
            "https://www.tiktok.com/t/ZTxxxxxx/",
            "https://www.tiktok.com/@username/video/7683885896365624596?is_from_webapp=1&sender_device=pc",
        ],
    )
    def test_valid_tiktok_urls(self, url: str):
        assert is_valid_tiktok_url(url) is True

    @pytest.mark.parametrize(
        "url",
        [
            "",
            "   ",
            "not_a_url",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://instagram.com/p/C-xxxx",
            "https://fake-tiktok.com/@user/video/1234567890123456789",
            "ftp://www.tiktok.com/@user/video/7683885896365624596",
            "https://tiktok.com/",
            "https://www.tiktok.com",
            None,
        ],
    )
    def test_invalid_urls(self, url: str):
        assert is_valid_tiktok_url(url) is False

    def test_short_urls(self):
        assert is_short_tiktok_url("https://vm.tiktok.com/ZMxxxxxx/") is True
        assert is_short_tiktok_url("https://vt.tiktok.com/ZSxxxxxx/") is True
        assert is_short_tiktok_url("https://www.tiktok.com/t/ZTxxxxxx/") is True
        assert is_short_tiktok_url("https://www.tiktok.com/@user/video/1234567890123456789") is False


class TestTikTokUrlExtraction:
    def test_extract_video_id(self):
        url = "https://www.tiktok.com/@riszzxpreset/video/7683885896365624596?is_from_webapp=1"
        assert extract_video_id_from_url(url) == "7683885896365624596"

    def test_extract_author(self):
        url = "https://www.tiktok.com/@riszzxpreset/video/7683885896365624596"
        assert extract_author_from_url(url) == "riszzxpreset"

    def test_extract_from_short_url_returns_none(self):
        url = "https://vm.tiktok.com/ZMxxxxxx/"
        assert extract_video_id_from_url(url) is None
        assert extract_author_from_url(url) is None


class TestTikTokUrlNormalization:
    def test_strip_tracking_parameters(self):
        url = "https://www.tiktok.com/@user/video/7683885896365624596?is_from_webapp=1&sender_device=pc&utm_source=share"
        normalized = normalize_tiktok_url(url)
        assert normalized == "https://www.tiktok.com/@user/video/7683885896365624596"

    def test_preserves_short_url(self):
        url = "http://vm.tiktok.com/ZMxxxxxx/?utm_source=copy"
        normalized = normalize_tiktok_url(url)
        assert normalized.startswith("https://vm.tiktok.com/ZMxxxxxx")
        assert "utm_source" not in normalized
