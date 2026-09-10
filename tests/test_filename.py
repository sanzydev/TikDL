from pathlib import Path
from core.filename import generate_download_filename
from providers.tiktok.models import TikTokVideoMetadata
from utils.files import ensure_unique_path, sanitize_filename


class TestFilenameSanitization:
    def test_sanitize_windows_invalid_chars(self):
        raw = 'user:name*with?invalid<chars>|and"quotes.mp4'
        clean = sanitize_filename(raw)
        assert ":" not in clean
        assert "*" not in clean
        assert "?" not in clean
        assert "<" not in clean
        assert ">" not in clean
        assert "|" not in clean
        assert '"' not in clean

    def test_sanitize_path_traversal(self):
        raw = "../../../etc/passwd.mp4"
        clean = sanitize_filename(raw)
        assert ".." not in clean
        assert "/" not in clean
        assert "\\" not in clean
        assert clean.endswith(".mp4")

    def test_windows_reserved_names(self):
        clean_con = sanitize_filename("CON.mp4")
        assert clean_con != "CON.mp4"
        assert "CON" in clean_con

        clean_aux = sanitize_filename("AUX.mp4")
        assert clean_aux != "AUX.mp4"

    def test_empty_string_uses_fallback(self):
        assert sanitize_filename("", fallback="video_default.mp4") == "video_default.mp4"
        assert sanitize_filename("   ", fallback="video_default.mp4") == "video_default.mp4"


class TestFilenameGeneration:
    def test_preferred_format_author_and_id(self):
        meta = TikTokVideoMetadata(
            id="123456789",
            author_username="john_doe",
            title="Cool video",
        )
        name = generate_download_filename(meta)
        assert name == "john_doe_123456789.mp4"

    def test_fallback_missing_author(self):
        meta = TikTokVideoMetadata(
            id="123456789",
            author_username="",
        )
        name = generate_download_filename(meta)
        assert name == "video_123456789.mp4"

    def test_fallback_missing_id(self):
        meta = TikTokVideoMetadata(
            id="",
            author_username="",
        )
        name = generate_download_filename(meta, timestamp=1700000000)
        assert name == "video_1700000000.mp4"

    def test_audio_format_extension(self):
        meta = TikTokVideoMetadata(
            id="123456789",
            author_username="musician",
        )
        name = generate_download_filename(meta, is_audio=True)
        assert name == "musician_123456789.mp3"


class TestDuplicateHandling:
    def test_avoid_overwriting(self, tmp_path: Path):
        initial_file = tmp_path / "john_123.mp4"
        initial_file.write_text("existing content")

        unique_path = ensure_unique_path(initial_file)
        assert unique_path.name == "john_123_1.mp4"
        assert not unique_path.exists()

        unique_path.write_text("existing content 2")
        third_path = ensure_unique_path(initial_file)
        assert third_path.name == "john_123_2.mp4"
