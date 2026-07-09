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


def test_skill_docs_checker_passes():
    check_docs = load_script("check_skill_docs.py")

    assert check_docs.main() == 0
