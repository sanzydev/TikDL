import json
import re
from typing import Any, Dict, List, Optional

from providers.tiktok.models import TikTokVideoMetadata
from utils.logging import get_logger

logger = get_logger("parser")

REHYDRATION_SCRIPT_RE = re.compile(
    r'<script\s+id=["\']__UNIVERSAL_DATA_FOR_REHYDRATION__["\']\s+type=["\']application/json["\']>(.*?)</script>',
    re.DOTALL,
)
SIGI_STATE_SCRIPT_RE = re.compile(
    r'<script\s+id=["\']SIGI_STATE__["\']\s+type=["\']application/json["\']>(.*?)</script>',
    re.DOTALL,
)
NEXT_DATA_SCRIPT_RE = re.compile(
    r'<script\s+id=["\']__NEXT_DATA__["\']\s+type=["\']application/json["\']>(.*?)</script>',
    re.DOTALL,
)
FRONTITY_SCRIPT_RE = re.compile(
    r'<script\s+id=["\']__FRONTITY_CONNECT_STATE__["\']\s+type=["\']application/json["\']>(.*?)</script>',
    re.DOTALL,
)


class TikTokParsingError(Exception):
    pass


class VideoUnavailableError(Exception):
    pass


class TikTokParser:
    @staticmethod
    def parse_html(html: str, expected_id: Optional[str] = None) -> TikTokVideoMetadata:
        if not html:
            raise TikTokParsingError("Received empty HTML content.")

        frontity_match = FRONTITY_SCRIPT_RE.search(html)
        if frontity_match:
            try:
                data = json.loads(frontity_match.group(1))
                return TikTokParser._parse_frontity_data(data, expected_id)
            except VideoUnavailableError:
                raise
            except Exception as exc:
                logger.debug(f"Failed parsing Frontity data: {exc}")

        rehydration_match = REHYDRATION_SCRIPT_RE.search(html)
        if rehydration_match:
            try:
                data = json.loads(rehydration_match.group(1))
                return TikTokParser._parse_rehydration_data(data, expected_id)
            except VideoUnavailableError:
                raise
            except Exception as exc:
                logger.debug(f"Failed parsing rehydration data: {exc}")

        sigi_match = SIGI_STATE_SCRIPT_RE.search(html)
        if sigi_match:
            try:
                data = json.loads(sigi_match.group(1))
                return TikTokParser._parse_sigi_state(data, expected_id)
            except VideoUnavailableError:
                raise
            except Exception as exc:
                logger.debug(f"Failed parsing SIGI_STATE data: {exc}")

        next_match = NEXT_DATA_SCRIPT_RE.search(html)
        if next_match:
            try:
                data = json.loads(next_match.group(1))
                return TikTokParser._parse_next_data(data, expected_id)
            except VideoUnavailableError:
                raise
            except Exception as exc:
                logger.debug(f"Failed parsing __NEXT_DATA__: {exc}")

        if "SlardarWAF" in html or "verify-center" in html or "tiktok-verify-page" in html:
            logger.debug("TikTok WAF verification detected in response.")
            raise VideoUnavailableError(
                "Access blocked by TikTok security verification or anti-bot challenge."
            )

        if "Video currently unavailable" in html or "Couldn't find this video" in html:
            raise VideoUnavailableError("The video is private, deleted, or unavailable.")

        raise TikTokParsingError(
            "Public metadata could not be extracted from this video page."
        )

    @staticmethod
    def _parse_frontity_data(data: Dict[str, Any], expected_id: Optional[str] = None) -> TikTokVideoMetadata:
        source_data = data.get("source", {}).get("data", {})
        target_vd = None
        for v in source_data.values():
            if isinstance(v, dict) and "videoData" in v:
                target_vd = v["videoData"]
                break

        if not target_vd:
            raise VideoUnavailableError("The video is private, deleted, or unavailable.")

        item_infos = target_vd.get("itemInfos", {})
        author_infos = target_vd.get("authorInfos", {})
        music_infos = target_vd.get("musicInfos", {})

        video_id = str(item_infos.get("id") or expected_id or "")
        desc = item_infos.get("text", "")
        author_username = author_infos.get("uniqueId", "")
        author_nickname = author_infos.get("nickName", "")

        video_obj = item_infos.get("video", {})
        video_meta = video_obj.get("videoMeta", {})
        duration = int(video_meta.get("duration", 0))
        width = video_meta.get("width")
        height = video_meta.get("height")
        ratio = str(video_meta.get("ratio", ""))

        photos = TikTokParser._extract_photos(target_vd)
        if not photos:
            photos = TikTokParser._extract_photos(item_infos)

        if (not width or width == 0) and target_vd.get("imagePostInfo", {}).get("displayImages"):
            first_img = target_vd["imagePostInfo"]["displayImages"][0]
            if isinstance(first_img, dict):
                width = first_img.get("width") or width
                height = first_img.get("height") or height

        resolution = TikTokParser._determine_resolution(ratio, width, height)

        video_urls = video_obj.get("urls", [])
        video_url = video_urls[0] if video_urls else None

        covers = item_infos.get("covers", [])
        thumbnail_url = covers[0] if covers else None

        music_urls = music_infos.get("playUrl", [])
        if isinstance(music_urls, list) and music_urls:
            audio_url = music_urls[0]
        elif isinstance(music_urls, str):
            audio_url = music_urls
        else:
            audio_url = None

        audio_title = music_infos.get("musicName", "")
        audio_author = music_infos.get("authorName", "")

        view_count = TikTokParser._safe_int(item_infos.get("playCount"))
        like_count = TikTokParser._safe_int(item_infos.get("diggCount"))
        comment_count = TikTokParser._safe_int(item_infos.get("commentCount"))
        share_count = TikTokParser._safe_int(item_infos.get("shareCount"))

        upload_date = str(item_infos.get("createTime", ""))
        title = desc.split("\n")[0].strip() if desc else f"Video by @{author_username}"

        return TikTokVideoMetadata(
            id=video_id,
            author_username=author_username,
            author_nickname=author_nickname,
            title=title,
            description=desc,
            duration=duration,
            resolution=resolution,
            width=width,
            height=height,
            thumbnail_url=thumbnail_url,
            upload_date=upload_date,
            view_count=view_count,
            like_count=like_count,
            comment_count=comment_count,
            share_count=share_count,
            video_url=video_url,
            audio_url=audio_url,
            audio_title=audio_title,
            audio_author=audio_author,
            photos=photos,
            is_private=False,
            is_available=True,
        )

    @staticmethod
    def _parse_rehydration_data(data: Dict[str, Any], expected_id: Optional[str] = None) -> TikTokVideoMetadata:
        default_scope = data.get("__DEFAULT_SCOPE__", {})
        video_detail = default_scope.get("webapp.video-detail", {})

        status_code = video_detail.get("statusCode", 0)
        if status_code != 0:
            status_msg = video_detail.get("statusMsg", "The video is private or unavailable.")
            logger.debug(f"Video detail statusCode {status_code}: {status_msg}")
            raise VideoUnavailableError("The video is private or unavailable.")

        item_info = video_detail.get("itemInfo", {})
        item_struct = item_info.get("itemStruct")

        if not item_struct:
            raise VideoUnavailableError("The video is private or unavailable.")

        if item_struct.get("privateItem") or item_struct.get("secret"):
            raise VideoUnavailableError("The video is private.")
        if item_struct.get("isProhibited") or item_struct.get("takeDown"):
            raise VideoUnavailableError("The video has been removed or deleted.")

        return TikTokParser._build_metadata_from_item_struct(item_struct, expected_id)

    @staticmethod
    def _parse_sigi_state(data: Dict[str, Any], expected_id: Optional[str] = None) -> TikTokVideoMetadata:
        item_module = data.get("ItemModule", {})
        if not item_module:
            raise VideoUnavailableError("The video is private or unavailable.")

        target_id = expected_id
        if not target_id or target_id not in item_module:
            target_id = next(iter(item_module.keys()), None)

        if not target_id:
            raise VideoUnavailableError("No video item found in page data.")

        item = item_module.get(target_id, {})
        if not item:
            raise VideoUnavailableError("The video is private or unavailable.")

        if item.get("secret") or item.get("privateItem"):
            raise VideoUnavailableError("The video is private.")

        return TikTokParser._build_metadata_from_sigi_item(item, target_id)

    @staticmethod
    def _parse_next_data(data: Dict[str, Any], expected_id: Optional[str] = None) -> TikTokVideoMetadata:
        props = data.get("props", {}).get("pageProps", {})
        item_info = props.get("itemInfo", {})
        item_struct = item_info.get("itemStruct")
        if not item_struct:
            raise VideoUnavailableError("The video is private or unavailable.")
        return TikTokParser._build_metadata_from_item_struct(item_struct, expected_id)

    @staticmethod
    def _build_metadata_from_item_struct(item: Dict[str, Any], fallback_id: Optional[str] = None) -> TikTokVideoMetadata:
        video_id = str(item.get("id") or fallback_id or "")
        desc = item.get("desc", "")

        author = item.get("author", {})
        author_username = author.get("uniqueId", "")
        author_nickname = author.get("nickname", "")

        video = item.get("video", {})
        duration = int(video.get("duration", 0))
        width = video.get("width")
        height = video.get("height")
        ratio = video.get("ratio", "")

        photos = TikTokParser._extract_photos(item)
        if (not width or width == 0) and photos:
            image_post = item.get("imagePost", {})
            img_list = image_post.get("images", []) if isinstance(image_post, dict) else []
            if img_list and isinstance(img_list[0], dict):
                first_img = img_list[0]
                img_u = first_img.get("imageURL") or first_img.get("displayImage") or {}
                if isinstance(img_u, dict):
                    w = img_u.get("width")
                    h = img_u.get("height")
                    if w and h:
                        width = w
                        height = h

        resolution = TikTokParser._determine_resolution(ratio, width, height)
        thumbnail_url = video.get("cover") or video.get("originCover") or video.get("dynamicCover")
        video_url = TikTokParser._extract_video_url(video)

        music = item.get("music", {})
        audio_url = music.get("playUrl")
        audio_title = music.get("title", "")
        audio_author = music.get("authorName", "")

        stats = item.get("stats", {})
        view_count = TikTokParser._safe_int(stats.get("playCount"))
        like_count = TikTokParser._safe_int(stats.get("diggCount"))
        comment_count = TikTokParser._safe_int(stats.get("commentCount"))
        share_count = TikTokParser._safe_int(stats.get("shareCount"))

        upload_date = str(item.get("createTime", ""))
        title = desc.split("\n")[0].strip() if desc else f"Video by @{author_username}"

        return TikTokVideoMetadata(
            id=video_id,
            author_username=author_username,
            author_nickname=author_nickname,
            title=title,
            description=desc,
            duration=duration,
            resolution=resolution,
            width=width,
            height=height,
            thumbnail_url=thumbnail_url,
            upload_date=upload_date,
            view_count=view_count,
            like_count=like_count,
            comment_count=comment_count,
            share_count=share_count,
            video_url=video_url,
            audio_url=audio_url,
            audio_title=audio_title,
            audio_author=audio_author,
            photos=photos,
            is_private=False,
            is_available=True,
        )

    @staticmethod
    def _build_metadata_from_sigi_item(item: Dict[str, Any], video_id: str) -> TikTokVideoMetadata:
        desc = item.get("desc", "")
        author_username = item.get("author", "")
        author_nickname = item.get("nickname", "")

        video = item.get("video", {})
        duration = int(video.get("duration", 0))
        width = video.get("width")
        height = video.get("height")
        ratio = video.get("ratio", "")

        photos = TikTokParser._extract_photos(item)

        resolution = TikTokParser._determine_resolution(ratio, width, height)
        thumbnail_url = video.get("cover") or video.get("dynamicCover")
        video_url = video.get("playAddr") or video.get("downloadAddr")

        music = item.get("music", {})
        audio_url = music.get("playUrl")

        stats = item.get("stats", {})
        view_count = TikTokParser._safe_int(stats.get("playCount"))
        like_count = TikTokParser._safe_int(stats.get("diggCount"))

        title = desc.split("\n")[0].strip() if desc else f"Video by @{author_username}"

        return TikTokVideoMetadata(
            id=video_id,
            author_username=author_username,
            author_nickname=author_nickname,
            title=title,
            description=desc,
            duration=duration,
            resolution=resolution,
            width=width,
            height=height,
            thumbnail_url=thumbnail_url,
            video_url=video_url,
            audio_url=audio_url,
            photos=photos,
            view_count=view_count,
            like_count=like_count,
            is_private=False,
            is_available=True,
        )

    @staticmethod
    def _extract_video_url(video_dict: Dict[str, Any]) -> Optional[str]:
        url = video_dict.get("playAddr") or video_dict.get("downloadAddr")
        if url:
            return url

        bitrate_info = video_dict.get("bitrateInfo", [])
        if bitrate_info:
            sorted_bitrates = sorted(
                bitrate_info,
                key=lambda x: x.get("Bitrate", 0) if isinstance(x, dict) else 0,
                reverse=True,
            )
            for entry in sorted_bitrates:
                play_addr = entry.get("PlayAddr", {})
                url_list = play_addr.get("UrlList", [])
                if url_list:
                    return url_list[0]

        return None

    @staticmethod
    def _determine_resolution(ratio: str, width: Optional[int], height: Optional[int]) -> str:
        if ratio and ("p" in ratio.lower() or "k" in ratio.lower()):
            return ratio

        if height and width:
            min_dim = min(width, height)
            if min_dim >= 1080:
                return "1080p"
            elif min_dim >= 720:
                return "720p"
            elif min_dim >= 480:
                return "480p"
            elif min_dim >= 360:
                return "360p"
            return f"{width}x{height}"

        return "1080p"

    @staticmethod
    def _safe_int(value: Any) -> Optional[int]:
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _extract_photos(data: Dict[str, Any]) -> List[str]:
        photos: List[str] = []
        image_list = []

        if "imagePostInfo" in data and isinstance(data["imagePostInfo"], dict):
            ipi = data["imagePostInfo"]
            if "displayImages" in ipi and isinstance(ipi["displayImages"], list):
                image_list.extend(ipi["displayImages"])
            elif "images" in ipi and isinstance(ipi["images"], list):
                image_list.extend(ipi["images"])

        if "imagePost" in data and isinstance(data["imagePost"], dict):
            ip = data["imagePost"]
            if "images" in ip and isinstance(ip["images"], list):
                image_list.extend(ip["images"])
            elif "displayImages" in ip and isinstance(ip["displayImages"], list):
                image_list.extend(ip["displayImages"])

        if "images" in data and isinstance(data["images"], list):
            image_list.extend(data["images"])

        for img in image_list:
            if isinstance(img, str) and img.startswith("http"):
                if img not in photos:
                    photos.append(img)
                continue
            if not isinstance(img, dict):
                continue
            urls = []
            if "urlList" in img and isinstance(img["urlList"], list):
                urls = img["urlList"]
            elif "imageURL" in img and isinstance(img["imageURL"], dict):
                urls = img["imageURL"].get("urlList", [])
            elif "displayImage" in img and isinstance(img["displayImage"], dict):
                urls = img["displayImage"].get("urlList", [])
            elif "url" in img and isinstance(img["url"], str):
                urls = [img["url"]]

            for u in urls:
                if u and isinstance(u, str) and u.startswith("http"):
                    if u not in photos:
                        photos.append(u)
                    break

        return photos
