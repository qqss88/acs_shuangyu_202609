# /// script
# requires-python = ">=3.10"
# dependencies = ["websockets>=12", "mutagen"]
# ///
"""Pre-generate Mandarin clips for index-xfyun.html with iFlytek (科大讯飞) online TTS.

Usage:
    uv run scripts/tts_xfyun.py [--vcn xiaoyan] [--force]

Credentials come from the environment or the git-ignored .env.local:
    XF_APPID=...  XF_API_KEY=...  XF_API_SECRET=...

Writes audio/xfyun/<hash>-n.mp3 (normal) and <hash>-s.mp3 (slow) plus audio/manifest.xfyun.js.
"""
import argparse
import base64
import hashlib
import hmac
import json
import os

import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_audio import ROOT, clip_id, extract_spoken_texts, write_manifest  # noqa: E402

HOST = "tts-api.xfyun.cn"
REQUEST_PATH = "/v2/tts"
HTML_PATH = ROOT / "index-xfyun.html"
CLIP_DIR = ROOT / "audio" / "xfyun"
MANIFEST_PATH = ROOT / "audio" / "manifest.xfyun.js"
ENV_PATH = ROOT / ".env.local"
CREDENTIAL_KEYS = ("XF_APPID", "XF_API_KEY", "XF_API_SECRET")

# iFlytek speed is 0-100 with 50 as normal; even 0 is only about 0.75x, so the page
# slows the "s" clip further for 0.5x/0.3x. The real factor is measured after generation.
SPEEDS = {"n": 50, "s": 0}
RECV_TIMEOUT_S = 20
MIN_CHARS_FOR_SPEED_MEASURE = 4


class XfyunError(RuntimeError):
    pass


def load_credentials() -> dict[str, str]:
    file_env: dict[str, str] = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and not key.strip().startswith("#"):
                file_env[key.strip()] = value.strip()
    creds = {k: os.environ.get(k) or file_env.get(k, "") for k in CREDENTIAL_KEYS}
    missing = [k for k, v in creds.items() if not v]
    if missing:
        sys.exit(f"Missing {', '.join(missing)}: set them in {ENV_PATH.name} or the environment")
    return creds


def signed_url(api_key: str, api_secret: str, now: datetime | None = None) -> str:
    """Build the HMAC-SHA256 signed WebSocket URL required by the iFlytek API."""
    date = format_datetime(now or datetime.now(timezone.utc), usegmt=True)
    origin = f"host: {HOST}\ndate: {date}\nGET {REQUEST_PATH} HTTP/1.1"
    digest = hmac.new(api_secret.encode(), origin.encode(), hashlib.sha256).digest()
    signature = base64.b64encode(digest).decode()
    auth = (
        f'api_key="{api_key}", algorithm="hmac-sha256", '
        f'headers="host date request-line", signature="{signature}"'
    )
    query = urlencode(
        {"authorization": base64.b64encode(auth.encode()).decode(), "date": date, "host": HOST}
    )
    return f"wss://{HOST}{REQUEST_PATH}?{query}"


def synthesize(creds: dict[str, str], text: str, vcn: str, speed: int) -> bytes:
    from websockets.sync.client import connect

    request = {
        "common": {"app_id": creds["XF_APPID"]},
        "business": {
            "aue": "lame",
            "sfl": 1,
            "auf": "audio/L16;rate=16000",
            "vcn": vcn,
            "speed": speed,
            "volume": 50,
            "pitch": 50,
            "tte": "UTF8",
        },
        "data": {"status": 2, "text": base64.b64encode(text.encode("utf-8")).decode()},
    }
    chunks: list[bytes] = []
    url = signed_url(creds["XF_API_KEY"], creds["XF_API_SECRET"])
    with connect(url, open_timeout=10) as ws:
        ws.send(json.dumps(request))
        while True:
            msg = json.loads(ws.recv(timeout=RECV_TIMEOUT_S))
            if msg.get("code") != 0:
                raise XfyunError(f"code {msg.get('code')}: {msg.get('message')} (sid {msg.get('sid')})")
            data = msg.get("data") or {}
            if data.get("audio"):
                chunks.append(base64.b64decode(data["audio"]))
            if data.get("status") == 2:
                break
    if not chunks:
        raise XfyunError(f"no audio returned for {text!r}")
    return b"".join(chunks)


def mp3_seconds(path: Path) -> float:
    from mutagen.mp3 import MP3

    return MP3(path).info.length


def measure_slow_factor(clips: dict[str, str]) -> float:
    """Ratio of normal to slow clip length over the longer clips, e.g. 0.65."""
    normal = slow = 0.0
    for text, cid in clips.items():
        if len(text) >= MIN_CHARS_FOR_SPEED_MEASURE:
            normal += mp3_seconds(CLIP_DIR / f"{cid}-n.mp3")
            slow += mp3_seconds(CLIP_DIR / f"{cid}-s.mp3")
    return round(normal / slow, 3) if slow else 0.6


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vcn", default="xiaoyan", help="iFlytek voice name (发音人)")
    parser.add_argument("--force", action="store_true", help="re-render clips that already exist")
    args = parser.parse_args()

    html = HTML_PATH.read_text(encoding="utf-8")
    texts = extract_spoken_texts(html)
    if not texts:
        sys.exit(f"No spoken text found in {HTML_PATH.name}; did the data format change?")
    creds = load_credentials()

    CLIP_DIR.mkdir(parents=True, exist_ok=True)
    clips: dict[str, str] = {}
    failures: list[str] = []
    for i, text in enumerate(texts, 1):
        cid = clip_id(f"xfyun|{args.vcn}|{SPEEDS}|{text}")
        clips[text] = cid
        for suffix, speed in SPEEDS.items():
            out = CLIP_DIR / f"{cid}-{suffix}.mp3"
            if out.exists() and not args.force:
                continue
            try:
                out.write_bytes(synthesize(creds, text, args.vcn, speed))
            except (XfyunError, OSError, TimeoutError) as err:
                failures.append(f"{text} ({suffix}): {err}")
        print(f"[{i}/{len(texts)}] {text}")

    if failures:
        sys.exit("Failed clips, manifest not written:\n  " + "\n  ".join(failures))

    used = {f"{cid}-{s}.mp3" for cid in clips.values() for s in SPEEDS}
    for stale in CLIP_DIR.glob("*.mp3"):
        if stale.name not in used:
            stale.unlink()

    slow_factor = measure_slow_factor(clips)
    write_manifest(
        args.vcn,
        clips,
        path=MANIFEST_PATH,
        clip_dir="audio/xfyun",
        speeds={"n": 1.0, "s": slow_factor},
    )
    print(f"Wrote {len(clips)} clips x {len(SPEEDS)} speeds, voice {args.vcn}, slow factor {slow_factor}")


if __name__ == "__main__":
    main()
