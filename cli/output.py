import json
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from core.metadata import MetadataService
from providers.tiktok.models import BatchSummary, DownloadResult, TikTokVideoMetadata

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(highlight=False)
err_console = Console(stderr=True, highlight=False)


class OutputHandler:
    def __init__(self, console_instance: Optional[Console] = None):
        self.console = console_instance or console

    def print_banner(self, version: str = "1.0.0") -> None:
        self.console.print(f"[bold cyan]TikDL[/bold cyan] [dim]v{version}[/dim]")

    def print_url_header(self, url: str) -> None:
        self.console.print("[dim]URL[/dim]")
        self.console.print(f"[blue underline]{url}[/blue underline]")

    def print_fetching_steps(self, validated: bool = True, public: bool = True, metadata: bool = True) -> None:
        self.console.print("[bold]Fetching[/bold]")
        if validated:
            self.console.print(" [green]✓[/green] URL validated")
        if public:
            self.console.print(" [green]✓[/green] Public video detected")
        if metadata:
            self.console.print(" [green]✓[/green] Metadata retrieved")

    def print_video_card(self, metadata: TikTokVideoMetadata, title_header: Optional[str] = None) -> None:
        data = MetadataService.get_display_card_data(metadata)

        header = title_header
        if not header:
            header = "PHOTOS" if (metadata.photos and not metadata.video_url) else "VIDEO"

        self.console.print(f"\n[bold]{header}[/bold]")
        self.console.print("[dim]────────────────────────────────[/dim]")
        for key, val in data.items():
            self.console.print(f"  [cyan]{key:<11}[/cyan] [white]{val}[/white]")
        self.console.print("[dim]────────────────────────────────[/dim]\n")

    def print_json(self, metadata: TikTokVideoMetadata) -> None:
        payload = MetadataService.get_json_payload(metadata)
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
        sys.stdout.flush()

    def print_error(self, message: str, reason: Optional[str] = None) -> None:
        err_console.print(f"[bold red]✗ {message}[/bold red]")
        if reason:
            err_console.print("[bold]Reason:[/bold]")
            err_console.print(f"[yellow]{reason}[/yellow]")

    def print_success_download(self, saved_path: Path, extra_paths: Optional[list] = None) -> None:
        self.console.print(" [green]✓[/green] [bold green]Download completed[/bold green]")
        self.console.print("[dim]Saved:[/dim]")
        if extra_paths and len(extra_paths) > 1:
            for p in extra_paths:
                self.console.print(f" [cyan]{p}[/cyan]")
            self.console.print()
        else:
            self.console.print(f" [cyan]{saved_path}[/cyan]\n")

    def print_batch_start(self, total: int) -> None:
        self.console.print(f"\n[bold]Found {total} URLs[/bold]")

    def print_batch_item_start(self, index: int, total: int, label: str) -> None:
        self.console.print(f"[[bold cyan]{index}/{total}[/bold cyan]] Downloading [white]{label}[/white]")

    def print_batch_item_result(self, result: DownloadResult) -> None:
        if result.success:
            self.console.print(" [green]✓ Completed[/green]")
        elif result.skipped:
            self.console.print(" [yellow]⚠ Skipped[/yellow]")
        else:
            self.console.print(f" [red]✗ Failed[/red] [dim]({result.error_message or 'Unknown error'})[/dim]")

    def print_batch_summary(self, summary: BatchSummary) -> None:
        self.console.print("\n[bold]Summary[/bold]")
        self.console.print("[dim]────────────────────────────────[/dim]")
        self.console.print(f"  [green]Completed[/green]  {summary.completed}")
        self.console.print(f"  [red]Failed[/red]     {summary.failed}")
        self.console.print(f"  [yellow]Skipped[/yellow]    {summary.skipped}")
        self.console.print("[dim]────────────────────────────────[/dim]\n")

    def create_progress(self) -> Progress:
        return Progress(
            TextColumn("[bold cyan]Downloading[/bold cyan]"),
            BarColumn(bar_width=24, complete_style="bold green", finished_style="bold green"),
            TextColumn("[bold green]{task.percentage:>3.0f}%[/bold green]"),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            transient=False,
        )
