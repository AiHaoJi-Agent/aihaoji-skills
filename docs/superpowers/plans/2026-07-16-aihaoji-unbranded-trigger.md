# Ai好记无品牌触发实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让未指定载体的个人笔记、笔记本和受支持详情意图无品牌触发 Ai好记，同时排除明确的本地文件、代码仓库和其他笔记服务，并用四平台矩阵验证路由与安全边界。

**Architecture:** frontmatter `description` 承担宿主发现阶段的正负路由，Skill 正文前置同一优先级规则和写操作确认边界。自动化测试锁定文档契约，宿主矩阵使用代表性自然语言用例，真实 API 只通过隔离测试授权执行只读工作流。

**Tech Stack:** Markdown Agent Skill、Python pytest、Node.js Skill 校验、Codex/OpenClaw/Claude Code/Hermes CLI。

## Global Constraints

- 未指定载体的个人笔记、个人笔记本和受支持详情意图默认触发 Ai好记。
- 明确指定本地文件、代码仓库、Obsidian、Notion、有道云笔记或其他服务时不触发 Ai好记。
- 导出个人笔记为 Markdown 属于 Ai好记；创建或修改本地 Markdown 文件不属于 Ai好记。
- 写操作确认、真实 ID、删除单独确认和回读规则不得弱化。
- 不记录 API Key、真实笔记正文或接口响应原文。
- 当前工作区包含既有未提交修改；本计划不自动提交或回退这些修改。

---

### Task 1: 增加无品牌触发契约测试

**Files:**
- Modify: `tests/test_scripts.py`
- Test: `tests/test_scripts.py`

**Interfaces:**
- Consumes: `SKILL_ROOT / "SKILL.md"`
- Produces: frontmatter 正向/负向触发和写确认的静态契约

- [ ] **Step 1: 写失败测试**

```python
def test_skill_defines_unbranded_trigger_and_explicit_carrier_exclusions():
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = skill.split("---", 2)[1]

    for phrase in (
        "Use when",
        "未指定载体",
        "个人笔记",
        "个人笔记本",
        "总结",
        "划线",
        "批注",
    ):
        assert phrase in frontmatter

    for phrase in (
        "本地文件",
        "代码仓库",
        "Obsidian",
        "Notion",
        "有道云笔记",
        "其他服务",
    ):
        assert phrase in frontmatter

    assert "## 触发边界" in skill
    assert "默认触发 Ai好记" in skill
    assert "只出现 `notes`、`folder`" in skill
    assert "导出个人笔记为 Markdown 仍属于本 Skill" in skill
    assert "本地 Markdown 文件则不属于本 Skill" in skill


def test_skill_trigger_expansion_preserves_write_confirmation():
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "路由到本 Skill 不等于授权写入" in skill
    assert "确认前不得调用写接口" in skill
    assert "写入前必须展示变更计划并等待用户确认" in skill
    assert "删除笔记本必须单独确认" in skill
```

- [ ] **Step 2: 验证测试按预期失败**

```bash
python3 -m pytest \
  tests/test_scripts.py::test_skill_defines_unbranded_trigger_and_explicit_carrier_exclusions \
  tests/test_scripts.py::test_skill_trigger_expansion_preserves_write_confirmation -q
```

Expected: FAIL，因为当前 frontmatter 仍要求品牌，正文没有 `## 触发边界`。

### Task 2: 最小修改 Skill 触发边界

**Files:**
- Modify: `skills/aihaoji/SKILL.md:1`
- Test: `tests/test_scripts.py`

**Interfaces:**
- Consumes: Task 1 的字符串契约
- Produces: 各宿主共享的无品牌触发与显式载体排除规则

- [ ] **Step 1: 替换 frontmatter description**

```yaml
description: Use when 未指定载体的用户要查询、阅读、导出、整理、移动或自动归类个人笔记，管理个人笔记本，或查看总结、大纲、全文、划线、批注和我的记录；提到 Ai好记 / AI好记 时也使用。明确指定本地文件、代码仓库、Obsidian、Notion、有道云笔记或其他服务时不要使用。
```

- [ ] **Step 2: 在开篇介绍后增加触发边界**

```markdown
## 触发边界

按以下优先级路由：

1. 用户明确指定操作对象位于本地文件、代码仓库、Obsidian、Notion、有道云笔记或其他服务时，服从指定载体，不触发本 Skill。
2. 未指定载体，且请求对象是个人笔记、个人笔记本或本 Skill 支持的笔记详情时，默认触发 Ai好记；无需出现“Ai好记”“AI好记”或 `aihaoji`。
3. 只出现 `notes`、`folder`、记录、文件或内容等宽泛词，不足以触发；源码、测试、接口字段和本地文件上下文均不属于个人笔记意图。

正向范围包括查询、搜索、导出、整理、移动和自动归类笔记，管理笔记本，以及查看总结、大纲、全文、原文、润色稿、划线、高亮、批注、我的记录和 AI 高亮。导出个人笔记为 Markdown 仍属于本 Skill；创建、读取或修改一个本地 Markdown 文件则不属于本 Skill。

路由到本 Skill 不等于授权写入：创建、重命名、移动、删除和自动归类前，必须先只读查询真实 ID、展示变更计划并等待明确确认；确认前不得调用写接口，删除笔记本仍须单独确认。
```

- [ ] **Step 3: 运行定向测试和 Skill 校验**

```bash
python3 -m pytest \
  tests/test_scripts.py::test_skill_defines_unbranded_trigger_and_explicit_carrier_exclusions \
  tests/test_scripts.py::test_skill_trigger_expansion_preserves_write_confirmation -q
npm run validate:skill
```

Expected: 2 passed；`Skill is valid!`。

### Task 3: 扩充公开兼容性矩阵

**Files:**
- Modify: `docs/agent-platform-compatibility.md`
- Modify: `tests/test_scripts.py`

**Interfaces:**
- Consumes: T1-T5、N1-N3、R1-R2、W1-W4、E1-E2
- Produces: 路由矩阵和安全工作流矩阵

- [ ] **Step 1: 先扩充矩阵测试断言**

```python
for scenario_id in (
    "T1", "T2", "T3", "T4", "T5",
    "N1", "N2", "N3",
    "R1", "R2",
    "W1", "W2", "W3", "W4",
    "E1", "E2",
):
    assert f"| {scenario_id} |" in matrix

assert "## 路由与误触发矩阵" in matrix
assert "## 安全与真实工作流矩阵" in matrix
```

- [ ] **Step 2: 运行测试并确认失败**

```bash
python3 -m pytest tests/test_scripts.py::test_public_agent_compatibility_matrix_covers_supported_workflows -q
```

Expected: FAIL，因为公开矩阵尚未包含新增场景和分层表格。

- [ ] **Step 3: 更新标准用例和结果表**

标准用例包括：T1 最近笔记、T2 无品牌 URL、T3 笔记本、T4 详情记录、T5 Markdown 导出、N1 仓库、N2 本地路径、N3 其他服务、R1/R2 真实只读、W1 创建、W2 移动、W3 自动归类、W4 删除、E1 权限不足和 E2 `429/5xx`。

使用两张结果表：`路由与误触发矩阵` 记录安装、T1-T5、N1-N3；`安全与真实工作流矩阵` 记录 R1-R2、W1-W4、E1-E2。未实际执行的新增项先标记 `未验证`。

- [ ] **Step 4: 运行定向测试**

```bash
python3 -m pytest tests/test_scripts.py::test_public_agent_compatibility_matrix_covers_supported_workflows -q
```

Expected: PASS。

### Task 4: 安装当前版本并执行四平台矩阵

**Files:**
- Modify: `docs/agent-platform-compatibility.md`
- Runtime only: `~/.agents/skills/aihaoji` 及宿主链接

**Interfaces:**
- Consumes: Task 2 的 Skill 和 Task 3 的用例
- Produces: 四个平台的实际版本、路由和安全结果

- [ ] **Step 1: 安装并核对主副本**

```bash
npx skills add . -g -y
shasum -a 256 \
  skills/aihaoji/SKILL.md \
  ~/.agents/skills/aihaoji/SKILL.md \
  ~/.openclaw/skills/aihaoji/SKILL.md \
  ~/.claude/skills/aihaoji/SKILL.md \
  ~/.hermes/skills/aihaoji/SKILL.md
```

Expected: 五个哈希一致。

- [ ] **Step 2: 创建隔离测试 HOME**

临时 HOME 只在 `.aihaoji/config.json` 中保存专用测试授权，并链接现有宿主配置和主 Skill；权限设为 `0600`，任何输出不得打印 Key。

- [ ] **Step 3: 执行平台新会话**

Codex 使用 `fork_turns="none"` 的隔离子任务逐条发送原始提示。其他宿主使用：

```bash
openclaw agent --local --session-id "$(uuidgen)" --json --message "$PROMPT"

SLASH_COMMAND_TOOL_CHAR_BUDGET=20000 \
claude -p --no-session-persistence --permission-mode plan --tools=Skill "$PROMPT"

hermes -z "$PROMPT"
```

每条用例使用全新会话。W1-W4 只检查计划与确认，不发送确认；任何写请求或直接声称完成均判失败。Claude debug 结果分开记录 Skill 扫描、description 预算、Skill 调用和确认等待。

- [ ] **Step 4: 更新矩阵**

记录实际版本：Codex `0.144.5`、OpenClaw `2026.7.1`、Claude Code `2.1.204`、Hermes 当前实际版本。记录日期、安装方式和失败类型，不固定记录动态 Skill 数量。

### Task 5: 使用专用授权执行真实只读工作流

**Files:**
- Modify: `docs/agent-platform-compatibility.md`
- Runtime only: 隔离测试 HOME

**Interfaces:**
- Consumes: 用户提供的专用测试授权
- Produces: R1、R2 的脱敏结论

- [ ] **Step 1: 执行 R1**

```bash
HOME="$TEST_HOME" \
AIHAOJI_API_KEY="$TEST_API_KEY" \
AIHAOJI_BASE_URL="$TEST_BASE_URL" \
npm run check
```

当前验证使用测试环境 `TEST_BASE_URL=https://openapi.readlecture.cn`；正式发布默认值仍为 `https://openapi.aihaoji.com`。Expected: 鉴权成功并完成最近笔记探测；输出不含 Key、ID 或正文。

- [ ] **Step 2: 执行 R2**

通过列表取得一个测试笔记 ID，再调用详情、`include_records=true` 和 `include_export_markdown=true`。输出只记录 HTTP/业务状态和目标字段是否存在，不打印 ID、标题、URL、记录或 Markdown 正文。

- [ ] **Step 3: 更新 R1/R2**

真实调用成功且满足脱敏要求才标记 `通过`；无样本或缺权限时记录实际边界。

### Task 6: 完整验证

**Files:**
- Verify only

- [ ] **Step 1: 运行项目规定命令**

```bash
npm test
python3 scripts/check_skill_docs.py
python3 -m compileall -q skills/aihaoji/scripts scripts/check_skill_docs.py tests/test_scripts.py
npm run validate:skill
npm pack --dry-run --json
git diff --check
```

Expected: 全部退出码为 0。

- [ ] **Step 2: 检查最终范围**

```bash
git status --short
git diff --stat
git diff -- skills/aihaoji/SKILL.md tests/test_scripts.py docs/agent-platform-compatibility.md docs/superpowers/specs/2026-07-16-aihaoji-unbranded-trigger-design.md docs/superpowers/plans/2026-07-16-aihaoji-unbranded-trigger.md
```

确认没有 API Key、真实笔记内容、临时测试文件或无关重构进入 diff。
