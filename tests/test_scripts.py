import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "aihaoji"


def load_script(name: str):
    base_dir = ROOT / "scripts" if name == "check_skill_docs.py" else SKILL_ROOT / "scripts"
    path = base_dir / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_install_helpers_normalize_base_url():
    install = load_script("install_aihaoji.py")

    assert install.normalize_base_url("https://openapi.aihaoji.com/") == "https://openapi.aihaoji.com"
    assert install.get_agent_open_api_base_url("https://example.com/") == "https://example.com/agent-open/api/v1"


def test_install_helpers_build_shared_config():
    install = load_script("install_aihaoji.py")

    config = install.write_shared_config(
        "sk-sxxx",
        "https://openapi.aihaoji.com/",
        {
            "user_id": "user_1",
            "user_name": "测试用户",
            "key_id": "key_1",
            "key_name": "默认密钥",
        },
    )

    assert config["provider"] == "aihaoji"
    assert config["apiKey"] == "sk-sxxx"
    assert config["baseUrl"] == "https://openapi.aihaoji.com"
    assert config["userId"] == "user_1"
    assert config["keyName"] == "默认密钥"


def test_install_writes_secret_config_with_owner_only_permissions(tmp_path):
    install = load_script("install_aihaoji.py")
    config_path = tmp_path / "config.json"

    install.save_json_config(config_path, {"apiKey": "sk-sxxx"})

    assert config_path.stat().st_mode & 0o777 == 0o600


def test_install_verify_summary_hides_internal_ids():
    install = load_script("install_aihaoji.py")
    result = install.summarize_verify_result(
        {
            "code": 0,
            "message": "success",
            "data": {
                "valid": True,
                "membership_active": True,
                "key_status": "active",
                "permissions": ["note:list", "folder:list"],
                "user_id": "user-secret",
                "key_id": "key-secret",
            },
        }
    )

    serialized = json.dumps(result)
    assert "user-secret" not in serialized
    assert "key-secret" not in serialized
    assert "user_id" not in serialized
    assert "key_id" not in serialized
    assert result["data"]["valid"] is True


def test_install_detects_current_codex_and_claude_code_skill_directories(monkeypatch, tmp_path):
    install = load_script("install_aihaoji.py")
    monkeypatch.setattr(install, "CODEX_CONFIG_PATH", tmp_path / "codex" / "config.toml")
    monkeypatch.setattr(install, "CODEX_SKILLS_PATH", tmp_path / "agents" / "skills")
    monkeypatch.setattr(install, "CLAUDE_CONFIG_PATH", tmp_path / "Library" / "Claude" / "config.json")
    monkeypatch.setattr(install, "CLAUDE_CODE_SKILLS_PATH", tmp_path / "claude" / "skills")
    monkeypatch.setattr(install, "HERMES_SKILLS_PATH", tmp_path / "hermes" / "skills")
    (tmp_path / "agents" / "skills").mkdir(parents=True)
    (tmp_path / "claude" / "skills").mkdir(parents=True)
    (tmp_path / "hermes" / "skills").mkdir(parents=True)

    hosts = install.detect_hosts()

    assert hosts["codex"] is True
    assert hosts["claude"] is True
    assert hosts["hermes"] is True


def test_install_detects_hermes_config_without_misreporting_claude_desktop(monkeypatch, tmp_path):
    install = load_script("install_aihaoji.py")
    monkeypatch.setattr(install, "CODEX_CONFIG_PATH", tmp_path / "codex" / "config.toml")
    monkeypatch.setattr(install, "CODEX_SKILLS_PATH", tmp_path / "agents" / "skills")
    monkeypatch.setattr(
        install,
        "CLAUDE_CONFIG_PATH",
        tmp_path / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
    )
    monkeypatch.setattr(install, "CLAUDE_CODE_SKILLS_PATH", tmp_path / "claude" / "skills")
    monkeypatch.setattr(install, "HERMES_SKILLS_PATH", tmp_path / "hermes" / "skills")
    monkeypatch.setattr(install, "HERMES_CONFIG_PATH", tmp_path / "hermes" / "config.yaml", raising=False)
    install.CLAUDE_CONFIG_PATH.parent.mkdir(parents=True)
    install.CLAUDE_CONFIG_PATH.write_text("{}", encoding="utf-8")
    install.HERMES_CONFIG_PATH.parent.mkdir(parents=True)
    install.HERMES_CONFIG_PATH.write_text(
        "skills:\n  external_dirs:\n    - ~/.agents/skills\n",
        encoding="utf-8",
    )

    hosts = install.detect_hosts()

    assert hosts["claude"] is False
    assert hosts["hermes"] is True


def test_install_verify_api_key_returns_none_on_http_error(monkeypatch):
    install = load_script("install_aihaoji.py")

    class FakeHTTPError(Exception):
        code = 403

        def read(self):
            return b'{"message":"missing scope"}'

    monkeypatch.setattr(install, "HTTPError", FakeHTTPError)

    def raise_error(_base_url, _api_key):
        raise FakeHTTPError()

    monkeypatch.setattr(install, "check_api_key", raise_error)

    assert install.verify_api_key("https://openapi.aihaoji.com", "sk-test") is None


def test_install_verify_api_key_rejects_business_failure(monkeypatch):
    install = load_script("install_aihaoji.py")
    monkeypatch.setattr(
        install,
        "check_api_key",
        lambda _base_url, _api_key: {
            "code": 40101,
            "message": "invalid key",
            "data": {
                "valid": False,
                "membership_active": False,
                "key_status": "disabled",
            },
        },
    )

    assert install.verify_api_key("https://openapi.aihaoji.com", "sk-test") is None


def test_check_aihaoji_builds_notes_probe_url():
    check = load_script("check_aihaoji.py")

    assert (
        check.build_notes_probe_url("https://openapi.aihaoji.com/")
        == "https://openapi.aihaoji.com/agent-open/api/v1/notes?page_no=1&page_size=1"
    )


def test_check_aihaoji_sends_raw_authorization_header(monkeypatch):
    check = load_script("check_aihaoji.py")
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"code":0}'

    def fake_urlopen(request, timeout):
        captured["authorization"] = request.get_header("Authorization")
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(check, "urlopen", fake_urlopen)

    assert check.http_json("https://example.com", "sk-sraw") == {"code": 0}
    assert captured == {"authorization": "sk-sraw", "timeout": 10}


def test_check_aihaoji_uses_shared_config_first(monkeypatch, tmp_path):
    check = load_script("check_aihaoji.py")
    shared_path = tmp_path / "shared.json"
    openclaw_path = tmp_path / "openclaw.json"
    shared_path.write_text(
        json.dumps({"apiKey": "sk-shared", "baseUrl": "https://shared.example.com/"}),
        encoding="utf-8",
    )
    openclaw_path.write_text(
        json.dumps(
            {
                "skills": {
                    "entries": {
                        "aihaoji": {
                            "apiKey": "sk-openclaw",
                            "env": {"AIHAOJI_BASE_URL": "https://openclaw.example.com"},
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(check, "SHARED_CONFIG_PATH", shared_path, raising=False)
    monkeypatch.setattr(check, "CONFIG_PATH", openclaw_path)

    assert check.load_skill_config() == ("sk-shared", "https://shared.example.com")


def test_check_aihaoji_shared_config_falls_back_when_openclaw_entry_is_missing(monkeypatch, tmp_path):
    check = load_script("check_aihaoji.py")
    shared_path = tmp_path / "shared.json"
    openclaw_path = tmp_path / "openclaw.json"
    shared_path.write_text(
        json.dumps({"apiKey": "sk-shared", "baseUrl": "https://shared.example.com/"}),
        encoding="utf-8",
    )
    openclaw_path.write_text(json.dumps({"skills": {"entries": {}}}), encoding="utf-8")
    monkeypatch.setattr(check, "SHARED_CONFIG_PATH", shared_path, raising=False)
    monkeypatch.setattr(check, "CONFIG_PATH", openclaw_path)

    assert check.load_skill_config() == ("sk-shared", "https://shared.example.com")


def test_check_aihaoji_valid_shared_config_ignores_malformed_openclaw_config(monkeypatch, tmp_path):
    check = load_script("check_aihaoji.py")
    shared_path = tmp_path / "shared.json"
    openclaw_path = tmp_path / "openclaw.json"
    shared_path.write_text(
        json.dumps({"apiKey": "sk-shared", "baseUrl": "https://shared.example.com/"}),
        encoding="utf-8",
    )
    openclaw_path.write_text("{broken", encoding="utf-8")
    monkeypatch.setattr(check, "SHARED_CONFIG_PATH", shared_path, raising=False)
    monkeypatch.setattr(check, "CONFIG_PATH", openclaw_path)

    assert check.load_skill_config() == ("sk-shared", "https://shared.example.com")


def test_check_aihaoji_probe_summary_hides_note_data():
    check = load_script("check_aihaoji.py")
    summary = check.summarize_notes_probe(
        {
            "code": 0,
            "message": "success",
            "data": {
                "total": 1,
                "page_no": 1,
                "page_size": 1,
                "notes": [
                    {
                        "note_id": "note-secret",
                        "folder_id": 42,
                        "title": "private title",
                    }
                ],
            },
        }
    )

    serialized = json.dumps(summary)
    assert "note-secret" not in serialized
    assert "private title" not in serialized
    assert "note_id" not in serialized
    assert "folder_id" not in serialized
    assert summary["data"] == {"total": 1, "page_no": 1, "page_size": 1, "note_count": 1}


def test_skill_docs_checker_passes():
    check_docs = load_script("check_skill_docs.py")

    assert check_docs.main() == 0


def test_skill_docs_use_parent_id_zero_for_root_folder_creation():
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    reference = (SKILL_ROOT / "references" / "agent-open-platform.md").read_text(encoding="utf-8")

    assert "顶层笔记本传 `parent_id=0`" in skill
    assert '"parent_id": 0' in reference
    assert "顶层笔记本传空" not in reference
    assert "`parent_id` 可为空，表示创建顶层笔记本" not in reference


def test_skill_uses_official_openclaw_primary_env_metadata():
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "metadata:\n  openclaw:\n    primaryEnv: AIHAOJI_API_KEY" in skill
    assert "metadata: {" not in skill
    assert "optionalEnv" not in skill
    frontmatter = skill.split("---", 2)[1]
    assert "requires:" not in frontmatter
    assert "baseUrl" not in frontmatter
    assert "homepage: https://openapi.aihaoji.com" in frontmatter
    assert "license: MIT-0" in frontmatter
    assert "compatibility:" not in frontmatter


def test_npm_package_uses_runtime_files_allowlist():
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

    assert package["files"] == [
        "README.md",
        "LICENSE",
        "skills/aihaoji/SKILL.md",
        "skills/aihaoji/agents/",
        "skills/aihaoji/references/",
        "skills/aihaoji/scripts/check_aihaoji.py",
        "skills/aihaoji/scripts/install_aihaoji.py",
        "skills/aihaoji/scripts/install.mjs",
    ]


def test_distributable_skill_uses_a_complete_nested_directory():
    assert not (ROOT / "SKILL.md").exists()
    for relative_path in (
        "SKILL.md",
        "references/agent-open-platform.md",
        "scripts/check_aihaoji.py",
        "scripts/install_aihaoji.py",
        "scripts/install.mjs",
        "agents/openai.yaml",
    ):
        assert (SKILL_ROOT / relative_path).is_file(), relative_path


def test_npm_cli_entrypoint_is_executable():
    install_script = SKILL_ROOT / "scripts" / "install.mjs"

    assert install_script.stat().st_mode & 0o111


def test_npm_package_avoids_host_specific_skill_metadata_and_install_lifecycle():
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

    assert "openclaw" not in package
    assert "clawhub" not in package
    assert "install" not in package["scripts"]
    assert "check:docs" not in package["scripts"]
    assert package["license"] == "MIT-0"
    assert package["engines"]["node"] == ">=18"


def test_skill_documents_host_install_locations_and_shared_config():
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for path in ("~/.agents/skills", "~/.claude/skills", "~/.aihaoji/config.json"):
        assert path in skill
        assert path in readme

    assert "~/.codex/skills" not in skill
    assert "~/.codex/skills" not in readme
    assert "~/.agents/skills" in readme
    assert "优先级高于 `~/.openclaw/skills`" in readme
    assert "npx skills add AiHaoJi-Agent/aihaoji-skills -g" in readme
    assert "-a codex" not in readme
    assert "-a claude-code" not in readme
    assert " -y" not in readme
    assert "Vercel Labs" not in readme
    assert "-a openclaw" not in readme
    assert "npx skills add" in readme
    assert "npm install -g aihaoji-skills" in readme


def test_skill_documents_hermes_shared_directory_support():
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    for content in (skill, readme):
        assert "Hermes Agent" in content
        assert "~/.hermes/config.yaml" in content
        assert "external_dirs" in content
        assert "~/.agents/skills" in content

    assert "hermes skills install https://github.com" not in skill
    assert "hermes skills install https://github.com" not in readme


def test_skill_hides_all_common_internal_ids_in_normal_output():
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    for field in ("note_id", "folder_id", "user_id", "key_id"):
        assert field in skill
    assert "普通展示默认隐藏" in skill


def test_license_and_codex_ui_metadata_match_distribution_targets():
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    openai_metadata = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")

    assert license_text.startswith("MIT No Attribution")
    assert "display_name: \"Ai好记\"" in openai_metadata
    assert "short_description:" in openai_metadata
    assert "default_prompt:" in openai_metadata


def test_readme_distinguishes_skill_install_from_key_setup():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "npx skills add AiHaoJi-Agent/aihaoji-skills -g" in readme
    assert "npx aihaoji-skills setup" in readme
    assert "npm install -g aihaoji-skills" in readme


def test_readme_documents_cross_host_update_and_reinstall_flow():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "npx skills update aihaoji -g" in readme
    assert "重新创建宿主链接" in readme
    assert "openclaw skills install" not in readme


def test_npm_package_and_cli_use_cross_host_name():
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    install_script = (SKILL_ROOT / "scripts" / "install.mjs").read_text(encoding="utf-8")
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert package["name"] == "aihaoji-skills"
    assert package["bin"] == {"aihaoji-skills": "./skills/aihaoji/scripts/install.mjs"}
    for content in (install_script, skill, readme):
        assert "aihaoji-openclaw" not in content
        assert "aihaoji-skills" in content


def test_skill_docs_keep_the_url_search_contract():
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    reference = (SKILL_ROOT / "references" / "agent-open-platform.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "按链接找笔记" in readme
    assert "按 URL 找笔记" in skill
    assert "支持按 URL 检索对应笔记" in reference
    assert "keyword=<完整 URL>" in reference
