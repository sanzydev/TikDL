import sys
import traceback
from pathlib import Path
from typing import List, Optional

from cli.output import OutputHandler
from cli.parser import CLIArgs
from config.settings import Settings, __version__, get_settings
from core.downloader import Downloader
from providers.tiktok.models import DownloadResult, TikTokVideoMetadata
from utils.logging import configure_logging, get_logger
from utils.urls import extract_author_from_url, extract_video_id_from_url, is_valid_tiktok_url

logger = get_logger("cli.commands")


def read_urls_from_file(file_path: Path) -> List[str]:
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    urls = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                urls.append(stripped)
    return urls


def run_app(args: CLIArgs, settings: Optional[Settings] = None) -> int:
    app_settings = settings or get_settings()

    if args.debug:
        app_settings.debug = True
    configure_logging(debug=app_settings.debug)

    output = OutputHandler()

    if args.output:
        app_settings.output_dir = args.output

    collected_urls: List[str] = list(args.urls)
    if args.file:
        try:
            file_urls = read_urls_from_file(args.file)
            collected_urls.extend(file_urls)
        except Exception as exc:
            output.print_error("Failed to read URL file", reason=str(exc))
            return 1

    if not collected_urls:
        output.print_banner(__version__)
        output.console.print("\n[yellow]No TikTok URLs provided.[/yellow]")
        output.console.print("Usage: [bold cyan]tiktokdl <URL>[/bold cyan] (view JSON)")
        output.console.print("       [bold cyan]tiktokdl <URL> -d[/bold cyan] (download video)")
        output.console.print("       [bold cyan]tiktokdl <URL> -a[/bold cyan] (download audio)\n")
        return 1

    if args.download or args.audio:
        with Downloader(settings=app_settings) as downloader:
            if len(collected_urls) == 1:
                return handle_single_download(
                    url=collected_urls[0],
                    output=output,
                    downloader=downloader,
                    is_audio=args.audio,
                    debug=args.debug,
                )
            else:
                return handle_batch_download(
                    urls=collected_urls,
                    output=output,
                    downloader=downloader,
                    is_audio=args.audio,
                    debug=args.debug,
                )

    return handle_json_mode(collected_urls, args.card, output, app_settings, debug=args.debug)


def handle_json_mode(
    urls: List[str],
    card_mode: bool,
    output: OutputHandler,
    settings: Settings,
    debug: bool = False,
) -> int:
    exit_code = 0
    with Downloader(settings=settings) as downloader:
        for url in urls:
            try:
                if not is_valid_tiktok_url(url):
                    if card_mode:
                        output.print_error("Invalid TikTok URL", reason=f"The URL '{url}' is not a supported public TikTok link.")
                    else:
                        sys.stderr.write(f"Invalid TikTok URL: {url}\n")
                    exit_code = 1
                    continue

                if card_mode:
                    output.print_banner(settings.version)
                    output.print_url_header(url)
                    output.print_fetching_steps(validated=True, public=True, metadata=True)

                metadata = downloader.fetch_info(url)

                if card_mode:
                    output.print_video_card(metadata)
                else:
                    output.print_json(metadata)

            except Exception as exc:
                exit_code = 1
                if debug:
                    traceback.print_exc()
                if card_mode:
                    output.print_error("Unable to retrieve video information", reason=str(exc))
                else:
                    sys.stderr.write(f"Error for {url}: {exc}\n")

    return exit_code


def handle_single_download(
    url: str,
    output: OutputHandler,
    downloader: Downloader,
    is_audio: bool,
    debug: bool = False,
) -> int:
    output.print_banner(downloader.settings.version)
    output.print_url_header(url)

    if not is_valid_tiktok_url(url):
        output.print_error(
            "Unable to download video",
            reason="The provided URL is not a recognized or supported public TikTok link.",
        )
        return 1

    metadata_holder: List[TikTokVideoMetadata] = []

    def on_metadata_received(meta: TikTokVideoMetadata) -> None:
        metadata_holder.append(meta)
        output.print_fetching_steps(validated=True, public=True, metadata=True)
        if is_audio:
            title_header = "AUDIO"
        elif meta.photos and not meta.video_url:
            title_header = "PHOTOS"
        else:
            title_header = "VIDEO"
        output.print_video_card(meta, title_header=title_header)

    progress_bar = output.create_progress()
    task_id = progress_bar.add_task("download", total=None)

    def on_progress(downloaded: int, total: Optional[int]) -> None:
        if total and total > 0:
            progress_bar.update(task_id, total=total, completed=downloaded)
        else:
            progress_bar.update(task_id, completed=downloaded)

    try:
        with progress_bar:
            result = downloader.download_single(
                url=url,
                is_audio=is_audio,
                progress_callback=on_progress,
                on_metadata=on_metadata_received,
            )

        if result.success and result.saved_path:
            output.print_success_download(result.saved_path, extra_paths=result.saved_paths)
            return 0
        else:
            output.print_error(
                "Unable to download media",
                reason=result.error_message or "The media is private, deleted, or unavailable.",
            )
            return 1

    except Exception as exc:
        if debug:
            traceback.print_exc()
        output.print_error("Unable to download video", reason=str(exc))
        return 1


def handle_batch_download(
    urls: List[str],
    output: OutputHandler,
    downloader: Downloader,
    is_audio: bool,
    debug: bool = False,
) -> int:
    output.print_banner(downloader.settings.version)
    output.print_batch_start(len(urls))

    def on_item_start(index: int, total: int, url: str) -> None:
        label = url
        author = extract_author_from_url(url)
        vid_id = extract_video_id_from_url(url)
        if author and vid_id:
            label = f"@{author}/{vid_id}"
        elif vid_id:
            label = f"video/{vid_id}"
        output.print_batch_item_start(index, total, label)

    def on_item_complete(index: int, total: int, result: DownloadResult) -> None:
        output.print_batch_item_result(result)

    summary = downloader.download_multiple(
        urls=urls,
        is_audio=is_audio,
        on_start=on_item_start,
        on_complete=on_item_complete,
    )

    output.print_batch_summary(summary)
    return 0 if summary.failed == 0 else 1
