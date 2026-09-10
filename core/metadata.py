from typing import Any, Dict

from providers.tiktok.models import TikTokVideoMetadata


class MetadataService:
    @staticmethod
    def format_duration(seconds: int) -> str:
        if not seconds or seconds <= 0:
            return "00:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def get_display_card_data(metadata: TikTokVideoMetadata) -> Dict[str, str]:
        author_display = f"@{metadata.author_username}" if metadata.author_username else "Unknown"
        title_display = metadata.title or metadata.description or "No title"
        if len(title_display) > 60:
            title_display = f"{title_display[:57]}..."

        duration_display = metadata.formatted_duration
        resolution_display = metadata.resolution or "1080p"

        data = {
            "Author": author_display,
            "Title": title_display,
            "Duration": duration_display,
            "Resolution": resolution_display,
        }

        if metadata.photos:
            data["Photos"] = f"{len(metadata.photos)} images"

        if metadata.view_count is not None:
            data["Views"] = f"{metadata.view_count:,}"

        return data

    @staticmethod
    def get_json_payload(metadata: TikTokVideoMetadata) -> Dict[str, Any]:
        return metadata.to_json_dict()
