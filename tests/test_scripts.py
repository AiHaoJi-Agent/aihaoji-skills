import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = ROOT / "scripts" / name
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


def test_check_aihaoji_builds_notes_probe_url():
    check = load_script("check_aihaoji.py")

    assert (
        check.build_notes_probe_url("https://openapi.aihaoji.com/")
        == "https://openapi.aihaoji.com/agent-open/api/v1/notes?page_no=1&page_size=1"
    )


def test_skill_docs_checker_passes():
    check_docs = load_script("check_skill_docs.py")

    assert check_docs.main() == 0


def test_skill_docs_use_parent_id_zero_for_root_folder_creation():
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    reference = (ROOT / "references" / "agent-open-platform.md").read_text(encoding="utf-8")

    assert "顶层笔记本传 `parent_id=0`" in skill
    assert '"parent_id": 0' in reference
    assert "顶层笔记本传空" not in reference
    assert "`parent_id` 可为空，表示创建顶层笔记本" not in reference
