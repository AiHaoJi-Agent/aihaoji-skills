#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://openapi.readlecture.cn"
OPENCLAW_CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"
SHARED_CONFIG_PATH = Path.home() / ".aihaoji" / "config.json"
CODEX_CONFIG_PATH = Path.home() / ".codex" / "config.toml"
CLAUDE_CONFIG_PATH = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
KEY_CREATE_URL = "https://openapi.readlecture.cn/zh/keys"


def normalize_base_url(base_url: str) -> str:
    return (base_url or DEFAULT_BASE_URL).rstrip("/")


def get_agent_open_api_base_url(base_url: str) -> str:
    return f"{normalize_base_url(base_url)}/agent-open/api/v1"


def get_agent_open_openapi_url(base_url: str) -> str:
    return f"{normalize_base_url(base_url)}/agent-open/openapi.json"


def fail(message: str) -> int:
    print(f"[error] {message}")
    return 1


def info(message: str) -> None:
    print(f"[info] {message}")


def load_config() -> dict:
    if OPENCLAW_CONFIG_PATH.exists():
        return json.loads(OPENCLAW_CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def save_json_config(config_path: Path, config: dict) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def check_backend(base_url: str) -> None:
    openapi_url = get_agent_open_openapi_url(base_url)
    req = Request(openapi_url)
    with urlopen(req, timeout=10) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Backend openapi check failed: {openapi_url}")


def check_api_key(base_url: str, api_key: str) -> dict:
    api_base_url = get_agent_open_api_base_url(base_url)
    req = Request(f"{api_base_url}/auth/verify", headers={"Authorization": api_key})
    with urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def write_skill_config(config: dict, api_key: str, base_url: str) -> dict:
    config.setdefault("skills", {})
    config["skills"].setdefault("entries", {})
    config["skills"]["entries"]["aihaoji"] = {
        "apiKey": api_key,
        "env": {
            "AIHAOJI_API_KEY": api_key,
            "AIHAOJI_BASE_URL": normalize_base_url(base_url),
        },
    }
    return config


def write_shared_config(api_key: str, base_url: str, verify_data: dict) -> dict:
    return {
        "provider": "aihaoji",
        "apiKey": api_key,
        "baseUrl": normalize_base_url(base_url),
        "userId": verify_data.get("user_id") or "",
        "userName": verify_data.get("user_name") or "",
        "keyId": verify_data.get("key_id") or "",
        "keyName": verify_data.get("key_name") or "",
    }


def detect_hosts() -> dict:
    return {
        "openclaw": OPENCLAW_CONFIG_PATH.parent.exists() or OPENCLAW_CONFIG_PATH.exists(),
        "codex": CODEX_CONFIG_PATH.parent.exists() or CODEX_CONFIG_PATH.exists(),
        "claude": CLAUDE_CONFIG_PATH.parent.exists() or CLAUDE_CONFIG_PATH.exists(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install Ai好记 OpenClaw skill config")
    parser.add_argument("--api-key", help="Existing Ai好记 agent open API key")
    parser.add_argument("--base-url", default=os.getenv("AIHAOJI_BASE_URL", DEFAULT_BASE_URL))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.base_url = normalize_base_url(args.base_url)

    if not args.api_key:
        info("当前还没有配置 Ai好记 API Key。")
        info(f"请先前往以下地址创建开发者密钥：{KEY_CREATE_URL}")
        return fail("Missing API key. Provide --api-key.")

    try:
        check_backend(args.base_url)
    except HTTPError as exc:
        return fail(f"Backend returned HTTP {exc.code} during openapi check.")
    except URLError as exc:
        return fail(f"Cannot connect backend: {exc}")
    except Exception as exc:
        return fail(str(exc))

    try:
        probe = check_api_key(args.base_url, args.api_key)
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            detail = payload.get("detail") or payload.get("message") or payload
            if isinstance(detail, dict) and detail.get("message"):
                return fail(str(detail["message"]))
            if isinstance(detail, str):
                return fail(detail)
        except Exception:
            pass
        return fail(f"API key verification failed with HTTP {exc.code}.")
    except URLError as exc:
        return fail(f"Cannot verify API key: {exc}")
    except Exception as exc:
        return fail(f"API key verification failed: {exc}")

    data = probe.get("data") or {}
    hosts = detect_hosts()
    shared_config = write_shared_config(args.api_key, args.base_url, data)
    save_json_config(SHARED_CONFIG_PATH, shared_config)

    if hosts["openclaw"]:
        config = load_config()
        config = write_skill_config(config, args.api_key, args.base_url)
        save_json_config(OPENCLAW_CONFIG_PATH, config)
        print(f"[ok] wrote OpenClaw config to {OPENCLAW_CONFIG_PATH}")
    else:
        print("[info] OpenClaw not detected, skipped writing OpenClaw config.")

    print(f"[ok] wrote shared config to {SHARED_CONFIG_PATH}")
    print(f"[ok] 当前用户是：{data.get('user_name') or data.get('user_id') or '未知用户'}")
    print(f"[ok] 已绑定密钥：{data.get('key_name') or data.get('key_id') or '未知密钥'}")
    print(f"[ok] 检测到宿主：OpenClaw={'yes' if hosts['openclaw'] else 'no'}, Codex={'yes' if hosts['codex'] else 'no'}, Claude={'yes' if hosts['claude'] else 'no'}")
    print("[ok] auth/verify 校验结果:")
    print(json.dumps(probe, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
