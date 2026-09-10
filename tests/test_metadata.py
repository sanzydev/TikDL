import pytest
from core.metadata import MetadataService
from providers.tiktok.models import TikTokVideoMetadata
from providers.tiktok.parser import (
    TikTokParser,
    TikTokParsingError,
    VideoUnavailableError,
)


class TestMetadataParsing:
    def test_parse_valid_rehydration_html(self, sample_html_with_rehydration: str):
        metadata = TikTokParser.parse_html(sample_html_with_rehydration)
        assert metadata.id == "7683885896365624596"
        assert metadata.author_username == "testuser"
        assert metadata.author_nickname == "Test Creator"
        assert metadata.duration == 32
        assert metadata.resolution == "1080p"
        assert metadata.video_url == "https://example.com/video.mp4"
        assert metadata.audio_url == "https://example.com/music.mp3"
        assert metadata.view_count == 9999
        assert metadata.like_count == 1234
        assert metadata.is_private is False
        assert metadata.is_available is True

    def test_parse_private_video_raises_unavailable(self, private_video_html: str):
        with pytest.raises(VideoUnavailableError) as exc_info:
            TikTokParser.parse_html(private_video_html)
        assert "private" in str(exc_info.value).lower()

    def test_parse_unavailable_video_raises_unavailable(self, unavailable_video_html: str):
        with pytest.raises(VideoUnavailableError) as exc_info:
            TikTokParser.parse_html(unavailable_video_html)
        assert "private" in str(exc_info.value).lower() or "unavailable" in str(exc_info.value).lower()

    def test_parse_waf_challenge_raises_unavailable(self, waf_challenge_html: str):
        with pytest.raises(VideoUnavailableError) as exc_info:
            TikTokParser.parse_html(waf_challenge_html)
        assert "verification" in str(exc_info.value).lower() or "anti-bot" in str(exc_info.value).lower()

    def test_parse_empty_html_raises_error(self):
        with pytest.raises(TikTokParsingError):
            TikTokParser.parse_html("")

    def test_parse_missing_fields_graceful_defaults(self):
        sparse_html = (
            '<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">\n'
            '{\n'
            '    "__DEFAULT_SCOPE__": {\n'
            '        "webapp.video-detail": {\n'
            '            "statusCode": 0,\n'
            '            "itemInfo": {\n'
            '                "itemStruct": {\n'
            '                    "id": "111222333",\n'
            '                    "video": {"duration": 15}\n'
            '                }\n'
            '            }\n'
            '        }\n'
            '    }\n'
            '}\n'
            '</script>'
        )
        metadata = TikTokParser.parse_html(sparse_html)
        assert metadata.id == "111222333"
        assert metadata.author_username == ""
        assert metadata.duration == 15
        assert metadata.view_count is None
        assert metadata.video_url is None


class TestMetadataFormattingAndJSON:
    def test_duration_formatting(self):
        assert MetadataService.format_duration(0) == "00:00"
        assert MetadataService.format_duration(27) == "00:27"
        assert MetadataService.format_duration(65) == "01:05"
        assert MetadataService.format_duration(3665) == "01:01:05"

    def test_json_payload_schema(self):
        meta = TikTokVideoMetadata(
            id="123456789",
            author_username="example",
            title="Example Video",
            duration=32,
            resolution="1080p",
            view_count=5000,
            photos=["https://example.com/p1.jpg", "https://example.com/p2.jpg"],
        )
        json_dict = meta.to_json_dict()
        assert json_dict["id"] == "123456789"
        assert json_dict["author"] == "example"
        assert json_dict["title"] == "Example Video"
        assert json_dict["duration"] == 32
        assert json_dict["resolution"] == "1080p"
        assert json_dict["views"] == 5000
        assert json_dict["photos"] == ["https://example.com/p1.jpg", "https://example.com/p2.jpg"]

    def test_parse_frontity_photo_data(self):
        photo_frontity_html = (
            '<script id="__FRONTITY_CONNECT_STATE__" type="application/json">\n'
            '{\n'
            '    "source": {\n'
            '        "data": {\n'
            '            "/video/7605900880998632725": {\n'
            '                "videoData": {\n'
            '                    "itemInfos": {\n'
            '                        "id": "7605900880998632725",\n'
            '                        "text": "Photo post description",\n'
            '                        "createTime": 1770886804,\n'
            '                        "covers": ["https://example.com/thumb.jpg"]\n'
            '                    },\n'
            '                    "authorInfos": {\n'
            '                        "uniqueId": "photocreator",\n'
            '                        "nickName": "Photo Creator"\n'
            '                    },\n'
            '                    "musicInfos": {},\n'
            '                    "imagePostInfo": {\n'
            '                        "displayImages": [\n'
            '                            {"width": 1920, "height": 1080, "urlList": ["https://example.com/img1.jpg"]},\n'
            '                            {"width": 1920, "height": 1080, "urlList": ["https://example.com/img2.jpg"]}\n'
            '                        ]\n'
            '                    }\n'
            '                }\n'
            '            }\n'
            '        }\n'
            '    }\n'
            '}\n'
            '</script>'
        )
        meta = TikTokParser.parse_html(photo_frontity_html, expected_id="7605900880998632725")
        assert meta.id == "7605900880998632725"
        assert meta.author_username == "photocreator"
        assert len(meta.photos) == 2
        assert meta.photos[0] == "https://example.com/img1.jpg"
        assert meta.photos[1] == "https://example.com/img2.jpg"
        assert meta.width == 1920
        assert meta.height == 1080
        assert meta.resolution == "1080p"
