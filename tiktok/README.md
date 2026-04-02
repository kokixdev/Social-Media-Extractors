# TikTok Extractor

Extract all public TikTok posts from a profile URL, filter them, export full metadata, and optionally download matching videos into one folder per post.

## Basic usage

Extract all available post links from a profile:

```bash
python3 tiktok_extractor.py "https://www.tiktok.com/@username"
```

That creates a default links file like:

```text
username_links.txt
```

## Download a complete profile

Download every matched post from the whole profile:

```bash
python3 tiktok_extractor.py "https://www.tiktok.com/@username" --download-videos
```

Choose custom output paths:

```bash
python3 tiktok_extractor.py "https://www.tiktok.com/@username" \
  --output outputs/tiktok_links.txt \
  --metadata-file outputs/tiktok_posts.csv \
  --download-videos \
  --download-dir downloads
```

## Filtering examples

Only keep posts with at least 50,000 views:

```bash
python3 tiktok_extractor.py "https://www.tiktok.com/@username" --min-views 50000
```

Only keep posts with at least 2,000 likes:

```bash
python3 tiktok_extractor.py "https://www.tiktok.com/@username" --min-likes 2000
```

Only keep stronger posts by engagement:

```bash
python3 tiktok_extractor.py "https://www.tiktok.com/@username" \
  --min-views 50000 \
  --min-likes 1500 \
  --min-comments 40 \
  --min-like-rate 0.025
```

Only keep recent posts from the last 30 days:

```bash
python3 tiktok_extractor.py "https://www.tiktok.com/@username" --max-age-days 30
```

Filter and download at the same time:

```bash
python3 tiktok_extractor.py "https://www.tiktok.com/@username" \
  --min-views 100000 \
  --min-likes 3000 \
  --download-videos \
  --metadata-file outputs/filtered_tiktok_posts.csv
```

## Metadata export

Export full metadata to CSV:

```bash
python3 tiktok_extractor.py "https://www.tiktok.com/@username" \
  --metadata-file outputs/tiktok_posts.csv
```

Export full metadata to JSON:

```bash
python3 tiktok_extractor.py "https://www.tiktok.com/@username" \
  --metadata-file outputs/tiktok_posts.json \
  --metadata-format json
```

The metadata export includes all fields returned by `yt-dlp` for each post. Nested values such as thumbnails or headers are serialized into CSV cells as JSON strings.

## Folder structure

When `--download-videos` is used:

```text
downloads/<username>/<date>_<video_id>/
  video.<ext>
  metadata.csv
```

Each post folder contains:

- the downloaded video file
- a one-row `metadata.csv` for that exact post

If some posts fail to download, the extractor continues and writes:

```text
downloads/<username>/failed_downloads.csv
```

## Full flag reference

| Flag | What it does |
| --- | --- |
| `source_url` | TikTok profile URL, such as `https://www.tiktok.com/@username` |
| `-o`, `--output` | Save matching post links to a custom text file |
| `--download-videos` | Download matching posts as video files |
| `--download-dir` | Base folder for downloaded post folders. Default: `downloads` |
| `--metadata-file` | Save combined metadata for all matched posts |
| `--metadata-format` | Metadata format for `--metadata-file`: `csv` or `json` |
| `--min-views` | Keep only posts with at least this many views |
| `--min-likes` | Keep only posts with at least this many likes |
| `--min-comments` | Keep only posts with at least this many comments |
| `--min-reposts` | Keep only posts with at least this many reposts |
| `--min-saves` | Keep only posts with at least this many saves |
| `--min-like-rate` | Keep only posts whose `likes / views` ratio is at least this value |
| `--max-age-days` | Keep only posts newer than this many days |

## Notes

- works best with public TikTok profiles
- suppresses repeated `yt-dlp` impersonation warning noise
- uses `--continue` and `--no-overwrites` when downloading
- continues when an individual post cannot be downloaded and logs the failure instead of aborting the whole batch
- writes only matched posts to the links file and metadata export
- photo posts and slideshows use a browser-backed fallback when TikTok slide images are not fully exposed by `yt-dlp`

## TikTok slideshow support

For TikTok photo posts, the extractor first tries the normal `yt-dlp` path.

If TikTok only exposes the cover image through `yt-dlp`, the extractor can fall back to a browser-backed TikTok scraper and fetch the full slide list from the page data.

This repo looks for an optional local virtual environment at:

```text
Social Media Extractors/.venv
```

If you want the strongest TikTok slideshow support on another machine, set up that virtual environment and install:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install TikTokApi playwright
.venv/bin/python -m playwright install chromium
```

## Help

```bash
python3 tiktok_extractor.py --help
```
