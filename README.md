# TikDL

Fast CLI tool to inspect metadata (JSON) and download public TikTok videos, photo albums, and audio.

Developed by [@sanzydev](https://github.com/sanzydev).

## Install

```bash
git clone https://github.com/sanzydev/TikDL.git
cd TikDL
pip install -r requirements.txt
```

Optionally install globally:
```bash
pip install -e .
```

## Usage

```bash
# View metadata as JSON (default, no download)
python main.py "https://www.tiktok.com/@user/video/1234567890"

# Download video (MP4) or photo album (JPG)
python main.py "https://www.tiktok.com/@user/video/1234567890" -d
python main.py "https://www.tiktok.com/@user/photo/1234567890" -d

# Download audio only (MP3)
python main.py "https://www.tiktok.com/@user/video/1234567890" -a

# Custom download directory
python main.py "https://www.tiktok.com/@user/video/1234567890" -d -o ./my_folder

# Batch download from list
python main.py -f urls.txt -d

# Visual card view
python main.py "https://www.tiktok.com/@user/video/1234567890" -c
```

## Options

| Flag | Description |
| :--- | :--- |
| `urls` | TikTok video or photo URL(s) |
| `-d, --download` | Download video (MP4) or photo album (JPG) |
| `-a, --audio` | Download audio track (MP3) |
| `-o, --output <dir>` | Destination folder (default: `./downloads`) |
| `-f, --file <file>` | Read URLs from a text file |
| `-c, --card` | Display terminal card instead of raw JSON |
| `--debug` | Enable verbose diagnostic logs |
| `-v, --version` | Show application version |

## Testing

```bash
python -m pytest tests/ -v
```

## License

MIT
