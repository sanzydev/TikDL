from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from config.settings import Settings
from core.downloader import Downloader
from network.http_client import HttpClient, TimeoutError
from providers.tiktok.client import TikTokClient
from providers.tiktok.models import TikTokVideoMetadata


class TestHttpClientMocked:
    @patch("httpx.Client.get")
    def test_get_retry_on_server_error_and_eventual_success(self, mock_get):
        fail_resp = MagicMock(status_code=502, reason_phrase="Bad Gateway")
        ok_resp = MagicMock(status_code=200, text="OK")
        mock_get.side_effect = [fail_resp, ok_resp]

        settings = Settings(max_retries=2, retry_backoff=0.01)
        client = HttpClient(settings=settings)
        resp = client.get("https://example.com")
        assert resp.status_code == 200
        assert mock_get.call_count == 2

    @patch("httpx.Client.get")
    def test_get_timeout_raises_timeout_error(self, mock_get):
        mock_get.side_effect = httpx.ReadTimeout("Read timed out")

        settings = Settings(max_retries=2, retry_backoff=0.01)
        client = HttpClient(settings=settings)
        with pytest.raises(TimeoutError):
            client.get("https://example.com")

    @patch("httpx.Client.stream")
    def test_stream_download_writes_file(self, mock_stream, tmp_path: Path):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Length": "1024"}
        mock_response.iter_bytes.return_value = [b"chunk1", b"chunk2", b"chunk3"]

        mock_stream.return_value.__enter__.return_value = mock_response

        client = HttpClient()
        target_path = tmp_path / "output.mp4"

        progress_calls = []

        def on_progress(downloaded, total):
            progress_calls.append((downloaded, total))

        saved = client.stream_download(
            url="https://example.com/stream.mp4",
            target_path=target_path,
            progress_callback=on_progress,
        )

        assert saved.exists()
        assert saved.read_bytes() == b"chunk1chunk2chunk3"
        assert len(progress_calls) == 3


class TestDownloaderMocked:
    def test_download_single_success(self, tmp_path: Path):
        meta = TikTokVideoMetadata(
            id="123456",
            author_username="testuser",
            title="A title",
            video_url="https://example.com/video.mp4",
            audio_url="https://example.com/audio.mp3",
        )

        mock_client = MagicMock(spec=TikTokClient)
        mock_client.fetch_metadata.return_value = meta

        mock_http = MagicMock(spec=HttpClient)
        saved_file = tmp_path / "testuser_123456.mp4"
        saved_file.write_bytes(b"dummy video data")
        mock_http.stream_download.return_value = saved_file

        downloader = Downloader(client=mock_client, http_client=mock_http)
        result = downloader.download_single(
            url="https://www.tiktok.com/@testuser/video/123456",
            output_dir=tmp_path,
        )

        assert result.success is True
        assert result.saved_path == saved_file
        assert result.file_size == len(b"dummy video data")
        mock_client.fetch_metadata.assert_called_once()
        mock_http.stream_download.assert_called_once()

    def test_download_audio_only(self, tmp_path: Path):
        meta = TikTokVideoMetadata(
            id="123456",
            author_username="testuser",
            title="A title",
            video_url="https://example.com/video.mp4",
            audio_url="https://example.com/audio.mp3",
        )

        mock_client = MagicMock(spec=TikTokClient)
        mock_client.fetch_metadata.return_value = meta

        mock_http = MagicMock(spec=HttpClient)
        saved_file = tmp_path / "testuser_123456.mp3"
        saved_file.write_bytes(b"dummy audio data")
        mock_http.stream_download.return_value = saved_file

        downloader = Downloader(client=mock_client, http_client=mock_http)
        result = downloader.download_single(
            url="https://www.tiktok.com/@testuser/video/123456",
            output_dir=tmp_path,
            is_audio=True,
        )

        assert result.success is True
        assert result.saved_path == saved_file
        assert str(result.saved_path).endswith(".mp3")
        mock_http.stream_download.assert_called_once()
        assert mock_http.stream_download.call_args[1]["url"] == "https://example.com/audio.mp3"

    def test_download_invalid_url_rejected(self):
        downloader = Downloader()
        result = downloader.download_single(url="https://youtube.com/watch?v=123")
        assert result.success is False
        assert "invalid" in result.error_message.lower()

    def test_batch_downloads(self, tmp_path: Path):
        meta = TikTokVideoMetadata(
            id="123456",
            author_username="testuser",
            video_url="https://example.com/video.mp4",
        )

        mock_client = MagicMock(spec=TikTokClient)
        mock_client.fetch_metadata.return_value = meta

        mock_http = MagicMock(spec=HttpClient)
        saved_file = tmp_path / "testuser_123456.mp4"
        saved_file.write_bytes(b"data")
        mock_http.stream_download.return_value = saved_file

        downloader = Downloader(client=mock_client, http_client=mock_http)

        urls = [
            "https://www.tiktok.com/@testuser/video/123456",
            "https://not-tiktok.com/video",
        ]

        summary = downloader.download_multiple(urls, output_dir=tmp_path)

        assert summary.total == 2
        assert summary.completed == 1
        assert summary.failed == 1
        assert len(summary.results) == 2

    def test_download_photos_success(self, tmp_path: Path):
        meta = TikTokVideoMetadata(
            id="7605900880998632725",
            author_username="photouser",
            title="A photo post",
            photos=["https://example.com/p1.jpg", "https://example.com/p2.jpg"],
        )

        mock_client = MagicMock(spec=TikTokClient)
        mock_client.fetch_metadata.return_value = meta

        mock_http = MagicMock(spec=HttpClient)
        img1 = tmp_path / "photouser_7605900880998632725_1.jpg"
        img2 = tmp_path / "photouser_7605900880998632725_2.jpg"
        img1.write_bytes(b"image1")
        img2.write_bytes(b"image2")
        mock_http.stream_download.side_effect = [img1, img2]

        downloader = Downloader(client=mock_client, http_client=mock_http)
        result = downloader.download_single(
            "https://www.tiktok.com/@photouser/photo/7605900880998632725",
            output_dir=tmp_path,
        )

        assert result.success is True
        assert len(result.saved_paths) == 2
        assert result.file_size == 12
        assert mock_http.stream_download.call_count == 2
