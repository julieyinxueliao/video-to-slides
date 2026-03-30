#!/usr/bin/env python3
"""
fetch_transcript.py — YouTube transcript + metadata fetcher
No API key required. Uses youtube-transcript-api + YouTube oEmbed.

Usage:
    python fetch_transcript.py <youtube_url_or_id>

Output (stdout): JSON with keys:
    video_id, title, channel, duration, language,
    transcript_text, transcript_timestamped

Exit codes:
    0 = success
    1 = error (details in JSON "error" field)
"""

import sys
import json
import re
import subprocess


def extract_video_id(url_or_id: str) -> str | None:
    patterns = [
        r'[?&]v=([A-Za-z0-9_-]{11})',
        r'youtu\.be/([A-Za-z0-9_-]{11})',
        r'embed/([A-Za-z0-9_-]{11})',
        r'^([A-Za-z0-9_-]{11})$',
    ]
    for p in patterns:
        m = re.search(p, url_or_id)
        if m:
            return m.group(1)
    return None


def get_metadata(video_id: str) -> dict:
    """YouTube oEmbed — public, no API key needed."""
    try:
        import urllib.request
        oembed_url = (
            f"https://www.youtube.com/oembed"
            f"?url=https://www.youtube.com/watch%3Fv%3D{video_id}&format=json"
        )
        with urllib.request.urlopen(oembed_url, timeout=10) as r:
            data = json.loads(r.read())
        return {
            "title":   data.get("title", ""),
            "channel": data.get("author_name", ""),
        }
    except Exception as e:
        return {"title": "", "channel": "", "_meta_error": str(e)}


def ensure_library():
    try:
        import youtube_transcript_api  # noqa: F401
    except ImportError:
        print("[fetch_transcript] Installing youtube-transcript-api...", file=sys.stderr)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "youtube-transcript-api", "-q"]
        )


def get_transcript(video_id: str) -> dict:
    ensure_library()
    from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    except TranscriptsDisabled:
        return {"error": "Transcripts are disabled for this video."}

    # Priority: manual captions > auto-generated, any language
    try:
        transcript = transcript_list.find_manually_created_transcript(
            ['zh', 'zh-Hans', 'zh-TW', 'zh-Hant', 'en', 'ja', 'ko', 'es', 'fr', 'de', 'pt', 'ar', 'hi']
        )
    except NoTranscriptFound:
        try:
            transcript = transcript_list.find_generated_transcript(
                ['zh', 'zh-Hans', 'zh-TW', 'zh-Hant', 'en', 'ja', 'ko', 'es', 'fr', 'de', 'pt', 'ar', 'hi']
            )
        except NoTranscriptFound:
            # Last resort: take whatever is available
            transcripts = list(transcript_list)
            if not transcripts:
                return {"error": "No transcripts available for this video."}
            transcript = transcripts[0]

    language_code = transcript.language_code
    entries = transcript.fetch()

    if not entries:
        return {"error": "Transcript fetched but is empty."}

    # Plain text (for analysis)
    plain_text = ' '.join(e['text'].strip() for e in entries if e['text'].strip())

    # Timestamped (for reference)
    def fmt_time(secs):
        m, s = divmod(int(secs), 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    timestamped = '\n'.join(
        f"[{fmt_time(e['start'])}] {e['text'].strip()}"
        for e in entries if e['text'].strip()
    )

    last = entries[-1]
    duration_secs = int(last['start'] + last.get('duration', 0))
    h, rem = divmod(duration_secs, 3600)
    m, s = divmod(rem, 60)
    duration_str = f"{h}h {m}m" if h else f"{m}m {s}s"

    return {
        "language":              language_code,
        "duration_seconds":      duration_secs,
        "duration":              duration_str,
        "transcript_text":       plain_text,
        "transcript_timestamped": timestamped,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python fetch_transcript.py <youtube_url_or_id>"}))
        sys.exit(1)

    raw = sys.argv[1]
    video_id = extract_video_id(raw)
    if not video_id:
        print(json.dumps({"error": f"Could not parse video ID from: {raw}"}))
        sys.exit(1)

    result = {"video_id": video_id}
    result.update(get_metadata(video_id))

    transcript_data = get_transcript(video_id)
    if "error" in transcript_data:
        result["transcript_error"] = transcript_data["error"]
    else:
        result.update(transcript_data)
        # Prefer duration from transcript over metadata
        if "duration" not in result:
            result["duration"] = transcript_data.get("duration", "unknown")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
