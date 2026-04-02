# Instagram Extractor

Extract public Instagram posts or reels from a profile URL, filter them, export readable post details, and optionally download matching media into one folder per post.

## Basic usage

Extract all available post links from a public profile:

```bash
python3 instagram_extractor.py "https://www.instagram.com/username/"
```

That creates a default links file like:

```text
username_links.txt
```

## Download a complete profile

Download all matched posts from the full profile:

```bash
python3 instagram_extractor.py "https://www.instagram.com/username/" --download-videos
```

Choose custom output paths:

```bash
python3 instagram_extractor.py "https://www.instagram.com/username/" \
  --output outputs/instagram_links.txt \
  --metadata-file outputs/instagram_posts.txt \
  --download-videos \
  --download-dir downloads
```

## Filtering examples

Only keep posts with at least 20,000 views:

```bash
python3 instagram_extractor.py "https://www.instagram.com/username/" --min-views 20000
```

Only keep posts with at least 1,000 likes:

```bash
python3 instagram_extractor.py "https://www.instagram.com/username/" --min-likes 1000
```

Only keep recent posts:

```bash
python3 instagram_extractor.py "https://www.instagram.com/username/" --max-age-days 30
```

Filter and download stronger posts:

```bash
python3 instagram_extractor.py "https://www.instagram.com/username/" \
  --min-views 25000 \
  --min-likes 1200 \
  --min-comments 20 \
  --min-like-rate 0.03 \
  --download-videos
```

## Details export

Export readable post details to text:

```bash
python3 instagram_extractor.py "https://www.instagram.com/username/" \
  --metadata-file outputs/instagram_posts.txt
```

## Folder structure

When `--download-videos` is used:

```text
downloads/<username>/<date>_<post_id>/
  video.<ext>
  details.txt
```

If some posts fail to download, the extractor continues and writes:

```text
downloads/<username>/failed_downloads.txt
```

## Full flag reference

| Flag | What it does |
| --- | --- |
| `source_url` | Instagram profile URL, such as `https://www.instagram.com/username/` |
| `-o`, `--output` | Save matching post links to a custom text file |
| `--download-videos` | Download matching posts as media files |
| `--download-dir` | Base folder for downloaded post folders. Default: `downloads` |
| `--metadata-file` | Save combined readable post details to a text file |
| `--min-views` | Keep only posts with at least this many views |
| `--min-likes` | Keep only posts with at least this many likes |
| `--min-comments` | Keep only posts with at least this many comments |
| `--min-reposts` | Keep only posts with at least this many reposts |
| `--min-saves` | Keep only posts with at least this many saves |
| `--min-like-rate` | Keep only posts whose `likes / views` ratio is at least this value |
| `--max-age-days` | Keep only posts newer than this many days |

## Notes

- works only for public profiles that `yt-dlp` can access
- Instagram changes access rules often, so some public profiles may still require login
- details exports include only the link, view count, like count, comment count, hashtags, and caption
- individual failed downloads are logged and skipped so the run can continue

## Help

```bash
python3 instagram_extractor.py --help
```
