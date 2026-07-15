#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://openapi.aihaoji.com"
CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"
SHARED_CONFIG_PATH = Path.home() / ".aihaoji" / "config.json"


def normalize_base_url(base_url: str) -> str:
    return (base_url if base_url else DEFAULT_BASE_URL).rstrip("/")


def get_agent_open_api_base_url(base_url: str) -> str:
    return f"{normalize_base_url(base_url)}/agent-open/api/v1"


def fail(message: str) -> int:
    print(f"[error] {message}")
    return 1


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_optional_json(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    value = json.loads(config_path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def get_skill_entry(config: dict) -> dict:
    entries = nested_dict(config, "skills", "entries")
    entry = entries.get("aihaoji")
    if not entry:
        raise KeyError("Missing skills.entries.aihaoji in openclaw.json")
    return entry


def nested_dict(value: dict, *keys: str) -> dict:
    current = value if isinstance(value, dict) else {}
    for key in keys:
        current = current.get(key, {})
        if not isinstance(current, dict):
            return {}
    return current


def http_json(url: str, api_key: str) -> dict:
    req = Request(url, headers={"Authorization": api_key})
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_skill_config() -> tuple[str, str]:
    try:
        shared_config = load_optional_json(SHARED_CONFIG_PATH)
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc

    shared_api_key = shared_config.get("apiKey")
    if shared_api_key:
        base_url = first_present(
            shared_config.get("baseUrl"),
            os.getenv("AIHAOJI_BASE_URL"),
            DEFAULT_BASE_URL,
        )
        return shared_api_key, normalize_base_url(base_url)

    try:
        openclaw_config = load_optional_json(CONFIG_PATH)
        entry = nested_dict(openclaw_config, "skills", "entries").get("aihaoji", {})
        if not isinstance(entry, dict):
            entry = {}
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc

    api_key = first_present(
        entry.get("apiKey"),
        os.getenv("AIHAOJI_API_KEY"),
    )
    if not api_key:
        raise RuntimeError("Missing Ai好记 API Key in shared config, OpenClaw config, or environment.")

    env = entry.get("env", {}) if isinstance(entry.get("env"), dict) else {}
    base_url = first_present(
        env.get("AIHAOJI_BASE_URL"),
        os.getenv("AIHAOJI_BASE_URL"),
        DEFAULT_BASE_URL,
    )
    return api_key, normalize_base_url(base_url)


def resolve_api_key(entry: dict) -> str:
    return first_present(entry.get("apiKey"), os.getenv("AIHAOJI_API_KEY"))


def resolve_base_url(entry: dict) -> str:
    env = entry.get("env", {})
    return normalize_base_url(
        first_present(env.get("AIHAOJI_BASE_URL"), os.getenv("AIHAOJI_BASE_URL"), DEFAULT_BASE_URL)
    )


def first_present(*values) -> str:
    for value in values:
        if value not in (None, ""):
            return value
    return ""


def build_notes_probe_url(base_url: str) -> str:
    query = urlencode({"page_no": 1, "page_size": 1})
    return f"{get_agent_open_api_base_url(base_url)}/notes?{query}"


def fetch_notes_probe(api_key: str, base_url: str) -> dict:
    url = build_notes_probe_url(base_url)
    try:
        return http_json(url, api_key)
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} when calling {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Cannot connect to {url}: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Unexpected error: {exc}") from exc


def summarize_notes_probe(result: dict) -> dict:
    data = result.get("data", {}) if isinstance(result, dict) else {}
    notes = data.get("notes", []) if isinstance(data, dict) else []
    return {
        "code": result.get("code"),
        "message": result.get("message"),
        "data": {
            "total": data.get("total"),
            "page_no": data.get("page_no"),
            "page_size": data.get("page_size"),
            "note_count": len(notes) if isinstance(notes, list) else 0,
        },
    }


def main() -> int:
    try:
        api_key, base_url = load_skill_config()
    except RuntimeError as exc:
        return fail(str(exc))

    try:
        result = fetch_notes_probe(api_key, base_url)
    except RuntimeError as exc:
        return fail(str(exc))

    print("[ok] notes endpoint reachable")
    print(json.dumps(summarize_notes_probe(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
