"""Run with: uv run --with pytest --with websockets --with mutagen pytest scripts"""
import base64
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from tts_xfyun import HOST, signed_url

FIXED = datetime(2026, 10, 17, 2, 53, 0, tzinfo=timezone.utc)


def test_signed_url_carries_host_date_and_authorization() -> None:
    url = urlparse(signed_url("key123", "secret456", FIXED))
    query = parse_qs(url.query)
    assert url.scheme == "wss" and url.netloc == HOST and url.path == "/v2/tts"
    assert query["host"] == [HOST]
    assert query["date"] == ["Sat, 17 Oct 2026 02:53:00 GMT"]
    auth = base64.b64decode(query["authorization"][0]).decode()
    assert auth.startswith('api_key="key123", algorithm="hmac-sha256", headers="host date request-line"')


def test_signature_is_deterministic_and_secret_dependent() -> None:
    assert signed_url("k", "s1", FIXED) == signed_url("k", "s1", FIXED)
    assert signed_url("k", "s1", FIXED) != signed_url("k", "s2", FIXED)


def test_secret_never_appears_in_url() -> None:
    assert "secret456" not in signed_url("key123", "secret456", FIXED)
