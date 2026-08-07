#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://openapi.aihaoji.com"
CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"
SHARED_CONFIG_PATH = Path.home() / ".aihaoji" / "config.json"
CREATE_PROBE_TITLE = "[Ai好记 Skill 自检] Markdown 创建与回读"
CREATE_PROBE_MARKDOWN = "## 二级标题\n\n### 三级标题\n\n- 列表项"
CREATE_PROBE_MARKERS = ("## 二级标题", "### 三级标题", "列表项")


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


def http_json(url: str, api_key: str, *, method: str = "GET", payload: dict | None = None) -> dict:
    headers = {"Authorization": api_key}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(url, data=data, headers=headers, method=method)
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


def build_create_note_url(base_url: str) -> str:
    return f"{get_agent_open_api_base_url(base_url)}/notes"


def build_full_readback_url(base_url: str, note_id: str) -> str:
    query = urlencode({"semantic_view": "full", "include_export_markdown": "true"})
    return f"{get_agent_open_api_base_url(base_url)}/notes/{quote(note_id, safe='')}?{query}"


def require_success(result: dict, operation: str) -> dict:
    if not isinstance(result, dict) or result.get("code") != 0:
        raise RuntimeError(f"{operation} failed")
    data = result.get("data")
    if not isinstance(data, dict):
        raise RuntimeError(f"{operation} returned invalid data")
    return data


def probe_http_json(
    url: str,
    api_key: str,
    operation: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
) -> dict:
    try:
        return http_json(url, api_key, method=method, payload=payload)
    except Exception as exc:
        raise RuntimeError(f"{operation} request failed") from exc


def run_create_probe(api_key: str, base_url: str, folder_id: int | None = None) -> dict:
    payload = {
        "title": CREATE_PROBE_TITLE,
        "content_markdown": CREATE_PROBE_MARKDOWN,
    }
    if folder_id is not None:
        payload["folder_id"] = folder_id

    create_data = require_success(
        probe_http_json(
            build_create_note_url(base_url),
            api_key,
            "Create probe",
            method="POST",
            payload=payload,
        ),
        "Create probe",
    )
    note_id = create_data.get("note_id")
    if not isinstance(note_id, str) or not note_id:
        raise RuntimeError("Create probe returned no note ID")

    readback_data = require_success(
        probe_http_json(build_full_readback_url(base_url, note_id), api_key, "Full readback probe"),
        "Full readback probe",
    )
    semantic_markdown = readback_data.get("semantic_markdown")
    export_markdown = readback_data.get("export_markdown")
    full_readback_ok = readback_data.get("semantic_view") == "full" and isinstance(semantic_markdown, str)
    markdown_hierarchy_ok = full_readback_ok and all(
        marker in semantic_markdown for marker in CREATE_PROBE_MARKERS
    )
    export_ok = isinstance(export_markdown, str) and all(
        marker in export_markdown for marker in CREATE_PROBE_MARKERS
    )
    if not full_readback_ok:
        raise RuntimeError("Full readback probe did not return the full Markdown view")
    if not markdown_hierarchy_ok:
        raise RuntimeError("Full readback probe lost Markdown hierarchy")
    if not export_ok:
        raise RuntimeError("Full readback probe returned an invalid Markdown export")

    return {
        "create_ok": True,
        "full_readback_ok": True,
        "markdown_hierarchy_ok": True,
        "export_ok": True,
    }


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="检查 Ai好记 Agent Open 接口可用性")
    parser.add_argument(
        "--create-probe",
        action="store_true",
        help="显式执行一次创建、full 回读和 Markdown 导出探针；需要 AIHAOJI_ALLOW_WRITE_PROBE=1",
    )
    parser.add_argument("--folder-id", type=int, help="创建探针使用的笔记本 ID")
    args = parser.parse_args(argv)

    if args.folder_id is not None and not args.create_probe:
        return fail("--folder-id requires --create-probe")
    if args.create_probe and os.getenv("AIHAOJI_ALLOW_WRITE_PROBE") != "1":
        return fail("写入探针需要显式设置 AIHAOJI_ALLOW_WRITE_PROBE=1")

    try:
        api_key, base_url = load_skill_config()
    except RuntimeError as exc:
        return fail(str(exc))

    if args.create_probe:
        try:
            result = run_create_probe(api_key, base_url, folder_id=args.folder_id)
        except RuntimeError as exc:
            return fail(str(exc))
        print("[ok] create/full readback probe passed")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    try:
        result = fetch_notes_probe(api_key, base_url)
    except RuntimeError as exc:
        return fail(str(exc))

    print("[ok] notes endpoint reachable")
    print(json.dumps(summarize_notes_probe(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
