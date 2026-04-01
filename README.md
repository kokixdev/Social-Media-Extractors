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
5. Optionally download matching videos into a structured folder tree

## Output structure

When `--download-videos` is used, each matched post gets its own folder:

```text
downloads/<source_name>/<post_folder>/
  video.<ext>
  metadata.csv
```

You can also export one combined metadata index with `--metadata-file`.

## Common features

- suppresses repeated `yt-dlp` impersonation warning noise
- keeps all available `yt-dlp` metadata fields in CSV and JSON exports
- stores nested metadata as JSON strings in CSV cells
- uses `--continue` and `--no-overwrites` when downloading

## Git behavior

The repo includes a `.gitignore` that excludes downloaded media and generated output files, so you can push only the scripts and documentation to GitHub.

## Platform folders

- [TikTok](./tiktok/README.md)
- [Instagram](./instagram/README.md)
- [YouTube](./youtube/README.md)
- [X](./x/README.md)
