# YouTube Extractor

Extract all public YouTube videos from a channel, handle, `/videos` page, or playlist URL, filter them, export full metadata, and optionally download matching videos into one folder per video.

## Basic usage

Extract all available video links from a channel:

```bash
python3 youtube_extractor.py "https://www.youtube.com/@channelname"
```

The extractor automatically normalizes a bare channel handle to the `videos` tab when needed.

## Download a complete channel or playlist

Download all videos from a channel:

```bash
python3 youtube_extractor.py "https://www.youtube.com/@channelname" --download-videos
```

Download from a playlist:

```bash
python3 youtube_extractor.py "https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID" --download-videos
```

Choose custom output paths:

```bash
python3 youtube_extractor.py "https://www.youtube.com/@channelname" \
  --output outputs/youtube_links.txt \
  --metadata-file outputs/youtube_posts.csv \
  --download-videos \
  --download-dir downloads
```

## Filtering examples

Only keep videos with at least 100,000 views:

```bash
python3 youtube_extractor.py "https://www.youtube.com/@channelname" --min-views 100000
```

Only keep videos with at least 5,000 likes:

```bash
python3 youtube_extractor.py "https://www.youtube.com/@channelname" --min-likes 5000
```

Only keep recent videos:

```bash
python3 youtube_extractor.py "https://www.youtube.com/@channelname" --max-age-days 90
```

Filter and download stronger videos:

```bash
python3 youtube_extractor.py "https://www.youtube.com/@channelname" \
  --min-views 250000 \
  --min-likes 8000 \
  --min-comments 200 \
  --download-videos
```

## Metadata export

Export full metadata to CSV:

```bash
python3 youtube_extractor.py "https://www.youtube.com/@channelname" \
  --metadata-file outputs/youtube_posts.csv
```

Export full metadata to JSON:

```bash
python3 youtube_extractor.py "https://www.youtube.com/@channelname" \
  --metadata-file outputs/youtube_posts.json \
  --metadata-format json
```

## Folder structure

When `--download-videos` is used:

```text
downloads/<channel>/<date>_<video_id>/
  video.<ext>
  metadata.csv
```

## Full flag reference

| Flag | What it does |
| --- | --- |
| `source_url` | YouTube channel, handle, `/videos` URL, or playlist URL |
| `-o`, `--output` | Save matching video links to a custom text file |
| `--download-videos` | Download matching videos |
| `--download-dir` | Base folder for downloaded video folders. Default: `downloads` |
| `--metadata-file` | Save combined metadata for all matched videos |
| `--metadata-format` | Metadata format for `--metadata-file`: `csv` or `json` |
| `--min-views` | Keep only videos with at least this many views |
| `--min-likes` | Keep only videos with at least this many likes |
| `--min-comments` | Keep only videos with at least this many comments |
| `--min-reposts` | Keep only videos with at least this many reposts when available |
| `--min-saves` | Keep only videos with at least this many saves when available |
| `--min-like-rate` | Keep only videos whose `likes / views` ratio is at least this value |
| `--max-age-days` | Keep only videos newer than this many days |

## Notes

- works with public channels and many playlist URLs
- a bare `@channel` URL is normalized to the channel videos tab automatically
- YouTube metadata is often richer than other platforms and usually includes more descriptive fields
- metadata exports include all fields `yt-dlp` returns for each video

## Help

```bash
python3 youtube_extractor.py --help
```
