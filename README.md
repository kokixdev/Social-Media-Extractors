# Social Media Extractors

This repository contains `yt-dlp`-based extractors for:

- TikTok
- Instagram
- YouTube
- X

Each platform folder contains:

- a platform-specific extractor script
- a platform-specific README

All scripts follow the same flow:

1. Extract all posts/videos from a public profile, channel, or account URL
2. Filter posts by metrics such as views, likes, comments, reposts, saves, and like rate
3. Export matching links to a text file
4. Export matching metadata to CSV or JSON
5. Optionally download matching media into a structured folder tree

## Requirements

- Python 3.12 or newer
- `yt-dlp` installed and available in your shell
- internet access for extraction and downloads

Optional for stronger TikTok slideshow/photo support:

- a local Python virtual environment in `.venv`
- `TikTokApi`
- `playwright`
- Chromium installed through Playwright

## Step-by-step setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd "Social Media Extractors"
```

### 2. Check Python

```bash
python3 --version
```

You should have Python 3.12 or newer.

### 3. Install `yt-dlp`

If `yt-dlp` is not already installed:

```bash
python3 -m pip install --user yt-dlp
```

Check that it works:

```bash
yt-dlp --version
```

### 4. Basic usage without optional TikTok slideshow support

At this point, all platform scripts can run:

```bash
python3 tiktok/tiktok_extractor.py "https://www.tiktok.com/@username"
python3 instagram/instagram_extractor.py "https://www.instagram.com/username/"
python3 youtube/youtube_extractor.py "https://www.youtube.com/@channelname"
python3 x/x_extractor.py "https://x.com/username"
```

### 5. Optional: enable stronger TikTok slideshow/photo extraction

This is only needed if you want the best chance of downloading all images from TikTok photo posts and slideshows.

Create a virtual environment:

```bash
python3 -m venv .venv
```

Install the required packages:

```bash
.venv/bin/python -m pip install TikTokApi playwright
```

Install Chromium for Playwright:

```bash
.venv/bin/python -m playwright install chromium
```

You do not need to activate the virtual environment manually for the extractor.
The TikTok extractor checks for `.venv` automatically and uses it for the slideshow fallback when available.

### 6. Verify the project

Run the help commands:

```bash
python3 tiktok/tiktok_extractor.py --help
python3 instagram/instagram_extractor.py --help
python3 youtube/youtube_extractor.py --help
python3 x/x_extractor.py --help
```

## Output structure

When `--download-videos` is used, each matched post gets its own folder:

```text
downloads/<source_name>/<post_folder>/
  video.<ext>
  metadata.csv
```

For slideshow or photo-style posts, the folder may contain:

```text
downloads/<source_name>/<post_folder>/
  image_1.jpg
  image_2.jpg
  image_3.jpg
  audio.m4a
  metadata.csv
```

If some posts fail to download, the run continues and writes:

```text
downloads/<source_name>/failed_downloads.csv
```

You can also export one combined metadata index with `--metadata-file`.

## Common features

- suppresses repeated `yt-dlp` impersonation warning noise
- keeps all available `yt-dlp` metadata fields in CSV and JSON exports
- stores nested metadata as JSON strings in CSV cells
- uses `--continue` and `--no-overwrites` when downloading
- continues past individual download failures and logs them to `failed_downloads.csv`

## Git behavior

The repo includes a `.gitignore` that excludes:

- downloaded media
- generated text, CSV, and JSON outputs
- local caches
- the optional `.venv`

That keeps Git focused on scripts and documentation only.

## Platform folders

- [TikTok](./tiktok/README.md)
- [Instagram](./instagram/README.md)
- [YouTube](./youtube/README.md)
- [X](./x/README.md)
