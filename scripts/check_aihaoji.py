#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://openapi.readlecture.cn"
CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"


def normalize_base_url(base_url: str) -> str:
    return (base_url or DEFAULT_BASE_URL).rstrip("/")


def get_agent_open_api_base_url(base_url: str) -> str:
    return f"{normalize_base_url(base_url)}/agent-open/api/v1"


def fail(message: str) -> int:
    print(f"[error] {message}")
    return 1


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def get_skill_entry(config: dict) -> dict:
    entries = ((config or {}).get("skills") or {}).get("entries") or {}
    entry = entries.get("aihaoji")
    if not entry:
        raise KeyError("Missing skills.entries.aihaoji in openclaw.json")
    return entry


def http_json(url: str, api_key: str) -> dict:
    req = Request(url, headers={"Authorization": api_key})
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    try:
        config = load_config()
        entry = get_skill_entry(config)
    except Exception as exc:
        return fail(str(exc))

    api_key = entry.get("apiKey") or os.getenv("AIHAOJI_API_KEY")
    if not api_key:
        return fail("Missing apiKey in OpenClaw config.")

    env = entry.get("env") or {}
    base_url = normalize_base_url(env.get("AIHAOJI_BASE_URL") or os.getenv("AIHAOJI_BASE_URL") or DEFAULT_BASE_URL)
    query = urlencode({"page_no": 1, "page_size": 1})
    url = f"{get_agent_open_api_base_url(base_url)}/notes?{query}"

    try:
        result = http_json(url, api_key)
    except HTTPError as exc:
        return fail(f"HTTP {exc.code} when calling {url}")
    except URLError as exc:
        return fail(f"Cannot connect to {url}: {exc}")
    except Exception as exc:
        return fail(f"Unexpected error: {exc}")

    print("[ok] notes endpoint reachable")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
