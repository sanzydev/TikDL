import json
from typing import Any, Dict
import pytest


@pytest.fixture
def sample_video_payload() -> Dict[str, Any]:
    return {
        "__DEFAULT_SCOPE__": {
            "webapp.video-detail": {
                "statusCode": 0,
                "itemInfo": {
                    "itemStruct": {
                        "id": "7683885896365624596",
                        "desc": "Example TikTok video title #fyp #trending",
                        "createTime": 1726000000,
                        "author": {
                            "uniqueId": "testuser",
                            "nickname": "Test Creator",
                        },
                        "video": {
                            "id": "7683885896365624596",
                            "height": 1080,
                            "width": 1440,
                            "duration": 32,
                            "ratio": "1080p",
                            "cover": "https://example.com/cover.jpg",
                            "playAddr": "https://example.com/video.mp4",
                            "downloadAddr": "https://example.com/video_dl.mp4",
                            "bitrateInfo": [
                                {
                                    "GearName": "original_1080_0",
                                    "Bitrate": 4919790,
                                    "PlayAddr": {
                                        "UrlList": ["https://example.com/video_high.mp4"]
                                    }
                                }
                            ]
                        },
                        "music": {
                            "id": "12345",
                            "title": "Sample Song",
                            "authorName": "Artist Name",
                            "playUrl": "https://example.com/music.mp3",
                        },
                        "stats": {
                            "diggCount": 1234,
                            "shareCount": 56,
                            "commentCount": 78,
                            "playCount": 9999,
                        },
                        "privateItem": False,
                        "secret": False,
                        "isProhibited": False,
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_html_with_rehydration(sample_video_payload: Dict[str, Any]) -> str:
    json_str = json.dumps(sample_video_payload)
    return (
        '<!DOCTYPE html><html><head>'
        f'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">{json_str}</script>'
        '</head><body><div>TikTok Page</div></body></html>'
    )


@pytest.fixture
def private_video_html() -> str:
    payload = {
        "__DEFAULT_SCOPE__": {
            "webapp.video-detail": {
                "statusCode": 10202,
                "statusMsg": "Video is private",
                "itemInfo": {}
            }
        }
    }
    return (
        '<!DOCTYPE html><html><head>'
        f'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">{json.dumps(payload)}</script>'
        '</head></html>'
    )


@pytest.fixture
def unavailable_video_html() -> str:
    payload = {
        "__DEFAULT_SCOPE__": {
            "webapp.video-detail": {
                "statusCode": 10204,
                "statusMsg": "Video does not exist",
                "itemInfo": {}
            }
        }
    }
    return (
        '<!DOCTYPE html><html><head>'
        f'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">{json.dumps(payload)}</script>'
        '</head></html>'
    )


@pytest.fixture
def waf_challenge_html() -> str:
    return (
        '<!DOCTYPE html><html><head>'
        '<script id="slardar-config" type="application/json">{"slardarClient": "SlardarWAF"}</script>'
        '</head><body>Please wait... <p class="_wafchallengeid"></p></body></html>'
    )

