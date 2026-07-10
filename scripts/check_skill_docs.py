#!/usr/bin/env python3
from pathlib import Path


REQUIRED_STRINGS = {
    "SKILL.md": [
        "name: aihaoji",
        "POST /agent-open/api/v1/folders",
        "POST /agent-open/api/v1/folders/batch-move",
        "PATCH /agent-open/api/v1/notes/{note_id}/folder",
        "GET /agent-open/api/v1/auth/verify",
        "AI 自动归类整理",
        "## 参数来源",
        "target_folder_id",
        "顶层笔记本传 `parent_id=0`",
        "move_item_list",
        "ai_highlights",
        "records_detail",
    ],
    "references/agent-open-platform.md": [
        "folder:write",
        "note:move",
        "POST /agent-open/api/v1/notes/batch-move",
        "POST /agent-open/api/v1/folders/batch-move",
        "include_records",
        '"target_folder_id": 123',
        '"parent_id": 0',
        "不要传 JSON `null`",
        "单篇移动传 `target_folder_id`",
        "move_item_list",
        "ai_highlights",
        "records_detail",
        "`target_folder_id` 必须来自",
    ],
    "README.md": [
        "自动归类整理",
        "划线、高亮、批注和我的记录",
        "移动整理笔记",
    ],
    "package.json": [
        "笔记本管理",
        "笔记整理",
        "批注",
    ],
}

FORBIDDEN_STRINGS = {
    "SKILL.md": [
        "GET /auth/verify",
    ],
    "references/agent-open-platform.md": [
        "GET /auth/verify",
        "GET /agent-open/api/v1/notes/{note_id}/records",
        "include_my_record",
        '"folder_id": 123\n}',
        "顶层笔记本传空",
        "`parent_id` 可为空，表示创建顶层笔记本",
    ],
}


def main() -> int:
    missing = collect_missing_checks()

    if missing:
        print("\n".join(missing))
        return 1

    print("[ok] Ai好记 skill docs cover organization and records capabilities")
    return 0


def collect_missing_checks() -> list[str]:
    missing: list[str] = []
    missing.extend(check_required_strings())
    missing.extend(check_forbidden_strings())
    missing.extend(check_skill_size())
    return missing


def check_required_strings() -> list[str]:
    missing: list[str] = []
    for file_name, needles in REQUIRED_STRINGS.items():
        text = Path(file_name).read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                missing.append(f"{file_name}: missing {needle}")
    return missing


def check_forbidden_strings() -> list[str]:
    missing: list[str] = []
    for file_name, needles in FORBIDDEN_STRINGS.items():
        text = Path(file_name).read_text(encoding="utf-8")
        for needle in needles:
            if needle in text:
                missing.append(f"{file_name}: forbidden {needle}")
    return missing



def check_skill_size() -> list[str]:
    skill_lines = Path("SKILL.md").read_text(encoding="utf-8").splitlines()
    if len(skill_lines) > 180:
        return [f"SKILL.md: too long ({len(skill_lines)} lines > 180)"]
    return []


if __name__ == "__main__":
    raise SystemExit(main())
