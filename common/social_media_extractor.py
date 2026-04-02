#!/usr/bin/env python3

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


WARNING_SNIPPETS = (
    "The extractor is attempting impersonation, but no impersonate target is available.",
    "If you encounter errors, then see  https://github.com/yt-dlp/yt-dlp#impersonation",
)


@dataclass
class VideoEntry:
    url: str
    video_id: str
    timestamp: int | None
    caption: str
    description: str
    duration: int
    uploader: str
    uploader_id: str
    channel: str
    channel_id: str
    track: str
    view_count: int
    like_count: int
    comment_count: int
    repost_count: int
    save_count: int
    raw_metadata: dict[str, Any]

    @property
    def like_rate(self) -> float:
        return self.like_count / self.view_count if self.view_count > 0 else 0.0


@dataclass
class DownloadFailure:
    video_id: str
    url: str
    post_folder: str
    error: str


def build_parser(platform_name: str, example_url: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            f"Extract {platform_name} post links from a profile/channel URL, "
            "filter posts by engagement, export readable post details, and optionally download videos."
        )
    )
    parser.add_argument(
        "source_url",
        help=f"{platform_name} profile/channel URL, for example {example_url}",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write matching post links to this file. Defaults to <source_name>_links.txt.",
    )
    parser.add_argument(
        "--download-videos",
        action="store_true",
        help="Download the matching videos after extracting and filtering the posts.",
    )
    parser.add_argument(
        "--download-dir",
        type=Path,
        default=Path("downloads"),
        help="Base directory used with --download-videos. Default: ./downloads",
    )
    parser.add_argument(
        "--metadata-file",
        type=Path,
        help="Export matching post details to this text file.",
    )
    parser.add_argument(
        "--min-views",
        type=int,
        default=0,
        help="Keep only posts with at least this many views.",
    )
    parser.add_argument(
        "--min-likes",
        type=int,
        default=0,
        help="Keep only posts with at least this many likes.",
    )
    parser.add_argument(
        "--min-comments",
        type=int,
        default=0,
        help="Keep only posts with at least this many comments.",
    )
    parser.add_argument(
        "--min-reposts",
        type=int,
        default=0,
        help="Keep only posts with at least this many reposts.",
    )
    parser.add_argument(
        "--min-saves",
        type=int,
        default=0,
        help="Keep only posts with at least this many saves.",
    )
    parser.add_argument(
        "--min-like-rate",
        type=float,
        default=0.0,
        help="Keep only posts whose likes/views ratio is at least this value, for example 0.03 for 3%%.",
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        help="Keep only posts newer than this many days.",
    )
    return parser


def derive_source_name(source_url: str) -> str:
    trimmed = source_url.split("?", 1)[0].rstrip("/")
    if not trimmed:
        return "source"
    if "/@" in trimmed:
        name = trimmed.rsplit("/@", 1)[1]
    else:
        name = trimmed.rsplit("/", 1)[-1]
    name = name.strip() or "source"
    return safe_name(name)


def normalize_source_url(platform_name: str, source_url: str) -> str:
    if platform_name.lower() == "tiktok":
        return normalize_tiktok_url(source_url)
    if platform_name.lower() != "youtube":
        return source_url
    lower_url = source_url.lower()
    youtube_domains = ("youtube.com/", "youtu.be/")
    if not any(domain in lower_url for domain in youtube_domains):
        return source_url
    tab_markers = ("/videos", "/shorts", "/streams", "/playlists", "/featured", "/live")
    terminal_markers = ("watch?", "playlist?", "/embed/", "/clip/")
    if any(marker in lower_url for marker in tab_markers + terminal_markers):
        return source_url
    return source_url.rstrip("/") + "/videos"


def normalize_tiktok_url(source_url: str) -> str:
    return re.sub(r"/photo/(\d+)", r"/video/\1", source_url)


def sanitize_stderr(stderr: str) -> str:
    lines = []
    for line in stderr.splitlines():
        if any(snippet in line for snippet in WARNING_SNIPPETS):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    command = ["yt-dlp", "--no-warnings", *args]
    return subprocess.run(command, text=True, capture_output=True)


def maybe_add_repo_venv_to_syspath() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    venv_lib = repo_root / ".venv" / "lib"
    if not venv_lib.exists():
        return
    candidates = sorted(venv_lib.glob("python*/site-packages"))
    for candidate in candidates:
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)


def get_tiktokapi_class():
    maybe_add_repo_venv_to_syspath()
    try:
        module = importlib.import_module("TikTokApi")
    except ImportError:
        return None
    return getattr(module, "TikTokApi", None)


async def _fetch_tiktok_photo_details_async(source_url: str) -> dict[str, Any]:
    TikTokApiClass = get_tiktokapi_class()
    if TikTokApiClass is None:
        raise RuntimeError("TikTokApi is not installed")
    async with TikTokApiClass() as api:
        await api.create_sessions(num_sessions=1, headless=True)
        video = api.video(url=normalize_tiktok_url(source_url))
        return await video.info()


def fetch_tiktok_photo_details(source_url: str) -> dict[str, Any]:
    try:
        return asyncio.run(_fetch_tiktok_photo_details_async(source_url))
    except RuntimeError as error:
        if "asyncio.run() cannot be called" in str(error):
            raise RuntimeError("TikTokApi fallback cannot run inside an active event loop") from error
        raise


def enrich_tiktok_photo_metadata(source_url: str, metadata: dict[str, Any]) -> dict[str, Any]:
    if "tiktok.com" not in source_url:
        return metadata
    if metadata.get("imagePost"):
        return metadata
    if has_video_format(metadata):
        return metadata
    try:
        enriched = fetch_tiktok_photo_details(source_url)
    except RuntimeError:
        return metadata
    if isinstance(enriched, dict) and enriched.get("imagePost"):
        return enriched
    return metadata


def fetch_post_details(source_url: str) -> dict[str, Any]:
    source_url = normalize_tiktok_url(source_url)
    result = run_command(["--skip-download", "--dump-single-json", source_url])
    if result.returncode != 0:
        error_text = sanitize_stderr(result.stderr) or "yt-dlp failed to fetch post details"
        raise RuntimeError(error_text)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"yt-dlp returned invalid post JSON: {error}") from error
    if not isinstance(payload, dict):
        raise RuntimeError("yt-dlp returned unexpected post metadata")
    return enrich_tiktok_photo_metadata(source_url, payload)


def fetch_profile_entries(source_url: str) -> list[VideoEntry]:
    source_url = normalize_tiktok_url(source_url)
    result = run_command(["--flat-playlist", "--dump-single-json", source_url])
    if result.returncode != 0:
        error_text = sanitize_stderr(result.stderr) or "yt-dlp failed to fetch profile data"
        raise RuntimeError(error_text)

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"yt-dlp returned invalid profile JSON: {error}") from error

    entries: list[VideoEntry] = []
    for raw_entry in iter_raw_entries(payload):
        url = raw_entry.get("url") or raw_entry.get("webpage_url") or raw_entry.get("original_url")
        video_id = raw_entry.get("id") or raw_entry.get("display_id")
        if not url or not video_id:
            continue
        entries.append(
            VideoEntry(
                url=normalize_tiktok_url(str(url)),
                video_id=str(video_id),
                timestamp=raw_entry.get("timestamp"),
                caption=str(raw_entry.get("title") or raw_entry.get("description") or ""),
                description=str(raw_entry.get("description") or ""),
                duration=int(raw_entry.get("duration") or 0),
                uploader=str(raw_entry.get("uploader") or ""),
                uploader_id=str(raw_entry.get("uploader_id") or ""),
                channel=str(raw_entry.get("channel") or ""),
                channel_id=str(raw_entry.get("channel_id") or ""),
                track=str(raw_entry.get("track") or ""),
                view_count=int(raw_entry.get("view_count") or 0),
                like_count=int(raw_entry.get("like_count") or 0),
                comment_count=int(raw_entry.get("comment_count") or 0),
                repost_count=int(raw_entry.get("repost_count") or 0),
                save_count=int(raw_entry.get("save_count") or 0),
                raw_metadata=dict(raw_entry),
            )
        )
    return dedupe_entries(entries)


def iter_raw_entries(payload: dict[str, Any]) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    stack = list(payload.get("entries", []))
    while stack:
        raw_entry = stack.pop(0)
        nested_entries = raw_entry.get("entries")
        if isinstance(nested_entries, list) and nested_entries:
            stack = nested_entries + stack
            continue
        collected.append(raw_entry)
    return collected


def dedupe_entries(entries: list[VideoEntry]) -> list[VideoEntry]:
    unique_entries: list[VideoEntry] = []
    seen = set()
    for entry in entries:
        dedupe_key = (entry.video_id, entry.url)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        unique_entries.append(entry)
    return unique_entries


def passes_filters(entry: VideoEntry, args: argparse.Namespace, now_utc: datetime) -> bool:
    if entry.view_count < args.min_views:
        return False
    if entry.like_count < args.min_likes:
        return False
    if entry.comment_count < args.min_comments:
        return False
    if entry.repost_count < args.min_reposts:
        return False
    if entry.save_count < args.min_saves:
        return False
    if entry.like_rate < args.min_like_rate:
        return False
    if args.max_age_days is not None:
        if entry.timestamp is None:
            return False
        cutoff = now_utc - timedelta(days=args.max_age_days)
        post_time = datetime.fromtimestamp(entry.timestamp, tz=timezone.utc)
        if post_time < cutoff:
            return False
    return True


def filter_entries(entries: list[VideoEntry], args: argparse.Namespace) -> list[VideoEntry]:
    now_utc = datetime.now(timezone.utc)
    return [entry for entry in entries if passes_filters(entry, args, now_utc)]


def timestamp_to_iso(timestamp: int | None) -> str:
    if timestamp is None:
        return ""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def safe_name(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in ("-", "_", ".") else "_" for char in value.strip())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "post"


def entry_date_prefix(entry: VideoEntry) -> str:
    if entry.timestamp is not None:
        return datetime.fromtimestamp(entry.timestamp, tz=timezone.utc).strftime("%Y%m%d")
    upload_date = entry.raw_metadata.get("upload_date")
    if isinstance(upload_date, str) and len(upload_date) == 8 and upload_date.isdigit():
        return upload_date
    return "unknown_date"


def entry_folder_name(entry: VideoEntry) -> str:
    return f"{entry_date_prefix(entry)}_{safe_name(entry.video_id)}"


def extract_hashtags(entry: VideoEntry) -> list[str]:
    tags: list[str] = []
    seen = set()

    for text in (entry.caption, entry.description):
        for match in re.findall(r"#([A-Za-z0-9_]+)", text or ""):
            tag = f"#{match}"
            if tag not in seen:
                seen.add(tag)
                tags.append(tag)

    challenges = entry.raw_metadata.get("challenges")
    if isinstance(challenges, list):
        for challenge in challenges:
            if not isinstance(challenge, dict):
                continue
            title = challenge.get("title") or challenge.get("chaName")
            if not isinstance(title, str) or not title.strip():
                continue
            tag = title if title.startswith("#") else f"#{title}"
            if tag not in seen:
                seen.add(tag)
                tags.append(tag)

    return tags


def display_caption(entry: VideoEntry) -> str:
    text = (entry.description or entry.caption or "").strip()
    return text or "(empty)"


def format_post_details(entry: VideoEntry) -> str:
    hashtags = extract_hashtags(entry)
    hashtag_text = ", ".join(hashtags) if hashtags else "(none)"
    lines = [
        f"Link: {entry.url}",
        f"Views: {entry.view_count}",
        f"Likes: {entry.like_count}",
        f"Comments: {entry.comment_count}",
        f"Hashtags: {hashtag_text}",
        "Caption:",
        display_caption(entry),
    ]
    return "\n".join(lines)


def write_metadata_text(path: Path, entries: list[VideoEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    blocks = [format_post_details(entry) for entry in entries]
    separator = "\n" + ("-" * 60) + "\n\n"
    content = separator.join(blocks)
    path.write_text(content + ("\n" if content else ""), encoding="utf-8")


def write_links(output_path: Path, entries: list[VideoEntry]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(entry.url for entry in entries) + ("\n" if entries else ""),
        encoding="utf-8",
    )


def collect_image_urls(metadata: dict[str, Any]) -> tuple[list[str], bool]:
    urls: list[str] = []
    seen = set()

    def add_url(value: Any) -> None:
        if not isinstance(value, str) or not value:
            return
        if value in seen:
            return
        seen.add(value)
        urls.append(value)

    image_list_keys = {
        "images",
        "image_list",
        "imageList",
        "photos",
        "photo_list",
        "photoList",
    }
    image_url_keys = {
        "url",
        "image_url",
        "imageUrl",
        "display_image",
        "displayImage",
        "origin_url",
        "originUrl",
    }
    image_url_list_keys = {"urllist", "url_list"}

    def walk(obj: Any, key_name: str | None = None) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                lower_key = key.lower()
                if lower_key in image_list_keys and isinstance(value, list):
                    for item in value:
                        walk(item, lower_key)
                    continue
                if lower_key in image_url_list_keys and isinstance(value, list):
                    if value:
                        add_url(value[0])
                    continue
                if lower_key in image_url_keys:
                    add_url(value)
                walk(value, lower_key)
        elif isinstance(obj, list):
            for item in obj:
                walk(item, key_name)

    walk(metadata)
    if urls:
        return urls, False

    thumbnail = metadata.get("thumbnail")
    add_url(thumbnail)

    thumbnails = metadata.get("thumbnails")
    if isinstance(thumbnails, list):
        for item in thumbnails:
            if isinstance(item, dict):
                thumb_id = str(item.get("id") or "").lower()
                if thumb_id in {"cover", "origincover", "thumbnail"}:
                    add_url(item.get("url"))

    return urls, True


def downloaded_video_candidates(post_dir: Path) -> list[Path]:
    return sorted(path for path in post_dir.iterdir() if path.is_file() and path.name.startswith("video."))


def rename_video_files_to_audio(post_dir: Path) -> list[Path]:
    renamed: list[Path] = []
    for path in downloaded_video_candidates(post_dir):
        target = post_dir / f"audio{path.suffix}"
        if target.exists():
            path.unlink(missing_ok=True)
            renamed.append(target)
            continue
        path.rename(target)
        renamed.append(target)
    return renamed


def file_suffix_from_url(url: str, default_suffix: str) -> str:
    parsed = urllib.parse.urlparse(url)
    suffix = Path(parsed.path).suffix
    if suffix:
        return suffix
    return default_suffix


def download_url_to_file(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request) as response, destination.open("wb") as handle:
            handle.write(response.read())
    except urllib.error.URLError as error:
        raise RuntimeError(f"failed to download {url}: {error}") from error


def has_video_format(metadata: dict[str, Any]) -> bool:
    formats = metadata.get("formats")
    if not isinstance(formats, list):
        return False
    for item in formats:
        if not isinstance(item, dict):
            continue
        vcodec = item.get("vcodec")
        if isinstance(vcodec, str) and vcodec not in ("none", ""):
            return True
    return False


def download_audio_only(entry_url: str, post_dir: Path) -> bool:
    result = run_command(
        [
            "--no-overwrites",
            "--continue",
            "-o",
            str(post_dir / "audio.%(ext)s"),
            entry_url,
        ]
    )
    return result.returncode == 0


def download_slideshow_assets(entry: VideoEntry, post_dir: Path, metadata: dict[str, Any]) -> bool:
    image_urls, cover_only = collect_image_urls(metadata)
    audio_downloaded = False

    if image_urls:
        for index, image_url in enumerate(image_urls, start=1):
            suffix = file_suffix_from_url(image_url, ".jpg")
            if cover_only:
                target_name = f"cover{suffix}"
            else:
                target_name = f"image_{index}{suffix}"
            download_url_to_file(image_url, post_dir / target_name)

    if not has_video_format(metadata):
        if not any(path.name.startswith("audio.") for path in post_dir.iterdir() if path.is_file()):
            audio_downloaded = download_audio_only(entry.url, post_dir)
        else:
            audio_downloaded = True

    return bool(image_urls or audio_downloaded)


def download_single_video(entry: VideoEntry, post_dir: Path) -> None:
    result = run_command(
        [
            "--no-overwrites",
            "--continue",
            "-o",
            str(post_dir / "video.%(ext)s"),
            entry.url,
        ]
    )
    try:
        metadata = fetch_post_details(entry.url)
    except RuntimeError:
        metadata = None

    if result.returncode == 0:
        if metadata is not None and not has_video_format(metadata):
            rename_video_files_to_audio(post_dir)
            if download_slideshow_assets(entry, post_dir, metadata):
                write_metadata_text(post_dir / "details.txt", [entry_from_metadata(entry.url, metadata)])
                return
            raise RuntimeError(f"post {entry.video_id} has no downloadable video format or slideshow assets")
        return

    if result.returncode != 0:
        try:
            if metadata is not None and download_slideshow_assets(entry, post_dir, metadata):
                write_metadata_text(post_dir / "details.txt", [entry_from_metadata(entry.url, metadata)])
                return
        except RuntimeError:
            pass
        error_text = sanitize_stderr(result.stderr) or f"yt-dlp failed to download video {entry.video_id}"
        raise RuntimeError(error_text)


def entry_from_metadata(entry_url: str, metadata: dict[str, Any]) -> VideoEntry:
    video_id = metadata.get("id") or metadata.get("display_id") or entry_url
    return VideoEntry(
        url=str(metadata.get("webpage_url") or metadata.get("original_url") or entry_url),
        video_id=str(video_id),
        timestamp=metadata.get("timestamp"),
        caption=str(metadata.get("title") or metadata.get("description") or ""),
        description=str(metadata.get("description") or ""),
        duration=int(metadata.get("duration") or 0),
        uploader=str(metadata.get("uploader") or ""),
        uploader_id=str(metadata.get("uploader_id") or ""),
        channel=str(metadata.get("channel") or ""),
        channel_id=str(metadata.get("channel_id") or ""),
        track=str(metadata.get("track") or ""),
        view_count=int(metadata.get("view_count") or 0),
        like_count=int(metadata.get("like_count") or 0),
        comment_count=int(metadata.get("comment_count") or 0),
        repost_count=int(metadata.get("repost_count") or 0),
        save_count=int(metadata.get("save_count") or 0),
        raw_metadata=dict(metadata),
    )


def write_failures_text(path: Path, failures: list[DownloadFailure]) -> None:
    blocks = []
    for failure in failures:
        blocks.append(
            "\n".join(
                [
                    f"Video ID: {failure.video_id}",
                    f"Link: {failure.url}",
                    f"Folder: {failure.post_folder}",
                    f"Error: {failure.error}",
                ]
            )
        )
    separator = "\n" + ("-" * 60) + "\n\n"
    content = separator.join(blocks)
    path.write_text(content + ("\n" if content else ""), encoding="utf-8")


def download_videos(entries: list[VideoEntry], download_dir: Path, source_name: str) -> Path:
    source_dir = download_dir / source_name
    source_dir.mkdir(parents=True, exist_ok=True)
    failures: list[DownloadFailure] = []

    for index, entry in enumerate(entries, start=1):
        post_dir = source_dir / entry_folder_name(entry)
        post_dir.mkdir(parents=True, exist_ok=True)
        write_metadata_text(post_dir / "details.txt", [entry])
        try:
            download_single_video(entry, post_dir)
            print(f"Downloaded {index}/{len(entries)} into {post_dir}")
        except RuntimeError as error:
            failures.append(
                DownloadFailure(
                    video_id=entry.video_id,
                    url=entry.url,
                    post_folder=post_dir.name,
                    error=str(error),
                )
            )
            print(f"Skipped {index}/{len(entries)} for {entry.video_id}: {error}", file=sys.stderr)

    if failures:
        write_failures_text(source_dir / "failed_downloads.txt", failures)
        print(f"Skipped {len(failures)} posts. See {source_dir / 'failed_downloads.txt'}")

    return source_dir


def print_summary(total_entries: int, matching_entries: list[VideoEntry], output_path: Path, metadata_path: Path | None) -> None:
    print(f"Found {total_entries} posts")
    print(f"Matched {len(matching_entries)} posts")
    print(f"Saved matching links to {output_path}")
    if metadata_path is not None:
        print(f"Saved matching post details to {metadata_path}")


def run_extractor(platform_name: str, example_url: str) -> int:
    parser = build_parser(platform_name, example_url)
    args = parser.parse_args()

    normalized_source_url = normalize_source_url(platform_name, args.source_url)
    source_name = derive_source_name(normalized_source_url)
    output_path = args.output or Path(f"{source_name}_links.txt")
    metadata_path = args.metadata_file

    try:
        entries = fetch_profile_entries(normalized_source_url)
        matching_entries = filter_entries(entries, args)
        write_links(output_path, matching_entries)
        if metadata_path is not None:
            write_metadata_text(metadata_path, matching_entries)
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print_summary(len(entries), matching_entries, output_path, metadata_path)

    if args.download_videos:
        if not matching_entries:
            print("No matching videos to download")
            return 0
        try:
            source_dir = download_videos(matching_entries, args.download_dir, source_name)
        except RuntimeError as error:
            print(f"Video download failed: {error}", file=sys.stderr)
            return 1
        print(f"Downloaded videos into {source_dir}")

    return 0
