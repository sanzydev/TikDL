import argparse
from pathlib import Path
from typing import List, Optional

from config.settings import __version__


class CLIArgs:
    def __init__(self, namespace: argparse.Namespace):
        self.urls: List[str] = namespace.urls or []
        self.file: Optional[Path] = Path(namespace.file) if namespace.file else None
        self.output: Optional[Path] = Path(namespace.output) if namespace.output else None
        self.download: bool = bool(namespace.download)
        self.audio: bool = bool(namespace.audio)
        self.card: bool = bool(namespace.card)
        self.json: bool = bool(namespace.json)
        self.debug: bool = bool(namespace.debug)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tiktokdl",
        description="TikDL - CLI metadata viewer and downloader for public TikTok videos.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "urls",
        nargs="*",
        help="One or more public TikTok video URLs.",
    )

    parser.add_argument(
        "-d", "--download",
        action="store_true",
        default=False,
        help="Download the video file locally.",
    )

    parser.add_argument(
        "-a", "--audio",
        action="store_true",
        default=False,
        help="Download the audio-only version (MP3).",
    )

    parser.add_argument(
        "-f", "--file",
        type=str,
        default=None,
        help="Read multiple URLs from a text file.",
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Specify destination folder for downloads (default: ./downloads).",
    )

    parser.add_argument(
        "-c", "--card",
        action="store_true",
        default=False,
        help="Display formatted visual card instead of raw JSON.",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Force JSON output format.",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable diagnostic logs.",
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"TikDL {__version__}",
        help="Show application version.",
    )

    return parser


def parse_args(args: Optional[List[str]] = None) -> CLIArgs:
    parser = build_parser()
    namespace = parser.parse_args(args)
    return CLIArgs(namespace)
