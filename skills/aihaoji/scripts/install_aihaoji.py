#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://openapi.aihaoji.com"
OPENCLAW_CONFIG_PATH = Path.home() / ".openclaw" / "openclaw.json"
SHARED_CONFIG_PATH = Path.home() / ".aihaoji" / "config.json"
CODEX_CONFIG_PATH = Path.home() / ".codex" / "config.toml"
CODEX_SKILLS_PATH = Path.home() / ".agents" / "skills"
CLAUDE_CONFIG_PATH = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
CLAUDE_CODE_SKILLS_PATH = Path.home() / ".claude" / "skills"
HERMES_SKILLS_PATH = Path.home() / ".hermes" / "skills"
HERMES_CONFIG_PATH = Path.home() / ".hermes" / "config.yaml"
KEY_CREATE_URL = "https://openapi.aihaoji.com"


def normalize_base_url(base_url: str) -> str:
    return first_present(base_url, default=DEFAULT_BASE_URL).rstrip("/")


def get_agent_open_api_base_url(base_url: str) -> str:
    return f"{normalize_base_url(base_url)}/agent-open/api/v1"


def fail(message: str) -> int:
    print(f"[error] {message}")
    return 1


def info(message: str) -> None:
    print(f"[info] {message}")


def first_present(*values, default=""):
    for value in values:
        if value not in (None, ""):
            return value
    return default


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def load_config() -> dict:
    if OPENCLAW_CONFIG_PATH.exists():
        return json.loads(OPENCLAW_CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def save_json_config(config_path: Path, config: dict) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(config, ensure_ascii=False, indent=2)
    descriptor = os.open(config_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as config_file:
        config_file.write(payload)
    os.chmod(config_path, 0o600)


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
        "userId": first_present(verify_data.get("user_id")),
        "userName": first_present(verify_data.get("user_name")),
        "keyId": first_present(verify_data.get("key_id")),
        "keyName": first_present(verify_data.get("key_name")),
    }


def detect_hosts() -> dict:
    return {
        "openclaw": any([OPENCLAW_CONFIG_PATH.parent.exists(), OPENCLAW_CONFIG_PATH.exists()]),
        "codex": any([CODEX_SKILLS_PATH.exists(), CODEX_CONFIG_PATH.parent.exists(), CODEX_CONFIG_PATH.exists()]),
        "claude": CLAUDE_CODE_SKILLS_PATH.exists(),
        "hermes": any([HERMES_SKILLS_PATH.exists(), HERMES_CONFIG_PATH.exists()]),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install Ai好记 OpenClaw skill config")
    parser.add_argument("--api-key", help="Existing Ai好记 agent open API key")
    parser.add_argument("--base-url", default=os.getenv("AIHAOJI_BASE_URL", DEFAULT_BASE_URL))
    return parser.parse_args()


def verify_api_key(base_url: str, api_key: str) -> dict | None:
    try:
        probe = check_api_key(base_url, api_key)
        data = probe.get("data", {}) if isinstance(probe, dict) else {}
        if not (
            probe.get("code") == 0
            and data.get("valid") is True
            and data.get("membership_active") is True
            and data.get("key_status") == "active"
        ):
            fail(first_present(probe.get("message"), default="API Key 校验失败。"))
            return None
        return probe
    except HTTPError as exc:
        message = extract_http_error_message(exc)
        if message:
            fail(message)
            return None
        fail(f"API key verification failed with HTTP {exc.code}.")
        return None
    except URLError as exc:
        fail(f"Cannot verify API key: {exc}")
        return None
    except Exception as exc:
        fail(f"API key verification failed: {exc}")
        return None


def extract_http_error_message(exc: HTTPError) -> str:
    try:
        payload = json.loads(exc.read().decode("utf-8"))
    except Exception:
        return ""

    detail = first_present(payload.get("detail"), payload.get("message"), payload)
    if isinstance(detail, dict) and detail.get("message"):
        return str(detail["message"])
    if isinstance(detail, str):
        return detail
    return ""


def write_detected_configs(api_key: str, base_url: str, verify_data: dict) -> dict:
    hosts = detect_hosts()
    shared_config = write_shared_config(api_key, base_url, verify_data)
    save_json_config(SHARED_CONFIG_PATH, shared_config)

    if hosts["openclaw"]:
        config = load_config()
        config = write_skill_config(config, api_key, base_url)
        save_json_config(OPENCLAW_CONFIG_PATH, config)
        print(f"[ok] wrote OpenClaw config to {OPENCLAW_CONFIG_PATH}")
    else:
        print("[info] OpenClaw not detected, skipped writing OpenClaw config.")

    print(f"[ok] wrote shared config to {SHARED_CONFIG_PATH}")
    return hosts


def summarize_verify_result(probe: dict) -> dict:
    data = probe.get("data", {}) if isinstance(probe, dict) else {}
    allowed_fields = ("valid", "membership_active", "key_status", "permissions")
    return {
        "code": probe.get("code"),
        "message": probe.get("message"),
        "data": {key: data.get(key) for key in allowed_fields if key in data},
    }


def print_install_summary(hosts: dict, verify_data: dict, probe: dict) -> None:
    user_label = first_present(verify_data.get("user_name"), default="已验证用户")
    key_label = first_present(verify_data.get("key_name"), default="已验证密钥")
    print(f"[ok] 当前用户是：{user_label}")
    print(f"[ok] 已绑定密钥：{key_label}")
    print(
        "[ok] 检测到宿主："
        f"OpenClaw={yes_no(hosts['openclaw'])}, "
        f"Codex={yes_no(hosts['codex'])}, "
        f"Claude={yes_no(hosts['claude'])}, "
        f"Hermes={yes_no(hosts['hermes'])}"
    )
    print("[ok] auth/verify 校验结果:")
    print(json.dumps(summarize_verify_result(probe), ensure_ascii=False, indent=2))


def main() -> int:
    args = parse_args()
    args.base_url = normalize_base_url(args.base_url)

    if not args.api_key:
        info("当前还没有配置 Ai好记 API Key。")
        info(f"请先前往以下地址创建开发者密钥：{KEY_CREATE_URL}")
        return fail("Missing API key. Provide --api-key.")

    info("使用 skill 仓库内静态接口文档 references/agent-open-platform.md")
    probe = verify_api_key(args.base_url, args.api_key)
    if probe is None:
        return 1

    data = first_present(probe.get("data"), default={})
    hosts = write_detected_configs(args.api_key, args.base_url, data)
    print_install_summary(hosts, data, probe)
    return 0


if __name__ == "__main__":
    sys.exit(main())
