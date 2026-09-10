# TikDL

<p align="center">
  <a href="https://pypi.org/project/tikdl/"><img src="https://img.shields.io/pypi/v/tikdl.svg?color=00f2fe&style=flat-square" alt="PyPI version"></a>
  <a href="https://pypi.org/project/tikdl/"><img src="https://img.shields.io/pypi/dm/tikdl?color=4facfe&style=flat-square" alt="PyPI downloads"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.12+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python 3.12+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License: MIT"></a>
  <a href="https://github.com/sanzydev/TikDL"><img src="https://img.shields.io/github/stars/sanzydev/TikDL?style=social" alt="GitHub Stars"></a>
</p>

<p align="center">
  <b>Fast, minimal CLI tool to inspect metadata (JSON) and download public TikTok videos, photo albums, and audio.</b>
</p>

<p align="center">
  Available for: <b>Python (PyPI)</b> | <a href="https://github.com/sanzydev/tikdl-js"><b>JavaScript / Node.js (npm)</b></a>
</p>

---

## Ecosystem

TikDL is available in both Python and JavaScript / Node.js implementations:

| Language | Registry | Quick Run / Install | Repository |
| :--- | :--- | :--- | :--- |
| **Python** | [![PyPI](https://img.shields.io/pypi/v/tikdl.svg?color=00f2fe&style=flat-square)](https://pypi.org/project/tikdl/) | `pip install tikdl` | [sanzydev/TikDL](https://github.com/sanzydev/TikDL) *(this repo)* |
| **JavaScript / Node.js** | [![npm](https://img.shields.io/npm/v/tikdl.svg?color=cb3837&style=flat-square)](https://www.npmjs.com/package/tikdl) | `npx tikdl <url>` | [sanzydev/tikdl-js](https://github.com/sanzydev/tikdl-js) |

---

## Architecture Flow

```mermaid
flowchart TD
    A[TikTok URL<br/>video or photo] --> B[TikDL Core Resolver]
    B --> C[Embed v2 & WAF Bypass Engine]
    C -->|Default| D[Pure JSON Metadata<br/>Direct media URLs & stats]
    C -->|Option -d| E[Downloader<br/>MP4 Video or JPG Photo Album]
    C -->|Option -a| F[Audio Extractor<br/>MP3 Audio Track]
    C -->|Option -c| G[Visual Terminal Card<br/>Rich formatted UI]
```

---

## Features

- **Zero Headless Browser Overhead** – No heavy Selenium, Playwright, or Chrome required. Powered by direct streaming HTTP client.
- **Built-in WAF Bypass** – Resilient against TikTok security challenges and anti-bot verification.
- **Full Photo Slideshow Support** – Extracts and batch downloads all high-resolution images from photo posts.
- **Direct Audio Download** – Grab public background audio tracks directly as `.mp3` with `-a`.
- **Pure JSON Metadata** – First-class JSON output format, ready for scripting or piping into `jq`.
- **Interactive Terminal UI** – Smooth download progress bars and styled visual cards powered by Rich.

---

## Installation

Install directly from **[PyPI](https://pypi.org/project/tikdl/)**:

```bash
pip install tikdl
```

Or install from source:

```bash
git clone https://github.com/sanzydev/TikDL.git
cd TikDL
pip install -e .
```

---

## Usage

### 1. View Metadata (JSON)
Outputs clean JSON without downloading any files:

```bash
tikdl "https://www.tiktok.com/@user/video/1234567890"
```

Pipe directly into `jq`:
```bash
tikdl "https://www.tiktok.com/@user/video/1234567890" | jq .video_url
```

### 2. Download Video or Photo Album (`-d`)
Downloads MP4 video file, or all JPG photos if the post is a slideshow:

```bash
# Download video
tikdl "https://www.tiktok.com/@user/video/1234567890" -d

# Download all photos from slideshow
tikdl "https://www.tiktok.com/@user/photo/1234567890" -d
```

### 3. Download Audio Only (`-a`)
Extracts and saves the background music track as `.mp3`:

```bash
tikdl "https://www.tiktok.com/@user/video/1234567890" -a
```

### 4. Visual Card View (`-c`)
Displays a formatted terminal summary card:

```bash
tikdl "https://www.tiktok.com/@user/video/1234567890" -c
```

### 5. Batch Download (`-f`)
Download multiple URLs from a text file:

```bash
tikdl -f urls.txt -d
```

---

## CLI Reference

| Flag | Description |
| :--- | :--- |
| `urls` | One or more TikTok video or photo URLs |
| `-d, --download` | Download video (MP4) or photo album (JPG) |
| `-a, --audio` | Download audio track only (MP3) |
| `-o, --output <dir>` | Destination directory (default: `./downloads`) |
| `-f, --file <file>` | Read URLs from text file (one URL per line) |
| `-c, --card` | Display visual terminal card instead of raw JSON |
| `--debug` | Enable verbose diagnostic logging |
| `-v, --version` | Show application version |

---

## Star History

<p align="center">
  <a href="https://star-history.dera.page/#sanzydev/TikDL&Date">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=sanzydev/TikDL&type=Date&theme=dark" />
      <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=sanzydev/TikDL&type=Date" />
      <img alt="TikDL Star History Chart" src="https://api.star-history.com/svg?repos=sanzydev/TikDL&type=Date" width="600" />
    </picture>
  </a>
</p>

---

## License

Distributed under the [MIT License](LICENSE). Developed by [@sanzydev](https://github.com/sanzydev).
