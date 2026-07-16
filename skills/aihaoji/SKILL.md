---
name: aihaoji
description: Use when the user asks about personal notes or personal notebooks without naming another storage target, including “最近的笔记” or “列出我的笔记本”, or wants to search, read, export, organize, move, or auto-classify notes and view 总结、大纲、全文、划线、批注 or 我的记录. These requests target the user's external note library, not agent memory and not Claude memory. Also use when Ai好记 / AI好记 is named. Do not use for explicit 本地文件 or Markdown, 代码仓库, Obsidian, Notion, 有道云笔记 or 其他服务.
license: MIT-0
metadata:
  openclaw:
    primaryEnv: AIHAOJI_API_KEY
    homepage: https://openapi.aihaoji.com
---

# Ai好记

通过 Ai好记 Agent Open Platform 查询、读取、导出和整理用户笔记。实际接口、字段和场景细节见 `references/agent-open-platform.md`；处理写入、记录读取、导出、自动归类或接口参数不确定时必须读取该参考。

## 触发边界

按以下优先级路由：

1. 用户明确指定操作对象位于本地文件、代码仓库、Obsidian、Notion、有道云笔记或其他服务时，服从指定载体，不触发本 Skill。
2. 未指定载体，且请求对象是个人笔记、个人笔记本或本 Skill 支持的笔记详情时，默认触发 Ai好记；这里指用户的外部个人笔记库，不是 Agent 或 Claude memory，无需出现“Ai好记”“AI好记”或 `aihaoji`。
3. 只出现 `notes`、`folder`、记录、文件或内容等宽泛词，不足以触发；源码、测试、接口字段和本地文件上下文均不属于个人笔记意图。

正向范围包括查询、搜索、导出、整理、移动和自动归类笔记，管理笔记本，以及查看总结、大纲、全文、原文、润色稿、划线、高亮、批注、我的记录和 AI 高亮。导出个人笔记为 Markdown 仍属于本 Skill；创建、读取或修改一个本地 Markdown 文件则不属于本 Skill。

路由到本 Skill 不等于授权写入：创建、重命名、移动、删除和自动归类前，必须先只读查询真实 ID、展示变更计划并等待明确确认；确认前不得调用写接口，删除笔记本仍须单独确认。

## 配置

优先从 `~/.aihaoji/config.json` 读取：

```json
{
  "apiKey": "sk-sxxxxxxxx",
  "baseUrl": "https://openapi.aihaoji.com"
}
```

缺失时再读 `$AIHAOJI_API_KEY` 和 `$AIHAOJI_BASE_URL`。请求头固定为：

```text
Authorization: $AIHAOJI_API_KEY
```

没有 API Key 时，引导用户去 `https://openapi.aihaoji.com` 创建 `sk-s...` 开发者密钥。用户可以直接在聊天中提供 Key，由当前 Agent 校验并写入共享配置；本机已安装 `aihaoji-skills` CLI 时，也可运行 `aihaoji-skills setup`。拿到 key 后先调 `GET /agent-open/api/v1/auth/verify` 校验，再写入权限为 `0600` 的 `~/.aihaoji/config.json`。自动配置失败时再提示用户使用可用的配置入口。

### 宿主安装位置

跨平台安装时，以 `~/.agents/skills/aihaoji` 作为全局主副本，不为每个宿主复制独立内容：

| 宿主 | 读取位置 | 说明 |
|---|---|---|
| Codex | `~/.agents/skills/aihaoji` | 最新官方用户级 Skill 目录 |
| OpenClaw | `~/.agents/skills/aihaoji` | personal-agent 来源，优先级高于 `~/.openclaw/skills` |
| Claude Code | `~/.claude/skills/aihaoji` | 链接到 `~/.agents/skills/aihaoji` |
| Hermes Agent | `~/.agents/skills/aihaoji` | 在 `~/.hermes/config.yaml` 的 `skills.external_dirs` 中启用 |

Hermes Agent 配置：

```yaml
skills:
  external_dirs:
    - ~/.agents/skills
```

`~/.aihaoji/config.json` 是 Codex、OpenClaw、Claude Code 和 Hermes Agent 共用的机器级 Key 配置，不属于任何宿主的 Skill 目录。用户可以在聊天中直接提供 Key，由当前 AI 写入该文件；写入后保持 `0600` 权限。Claude Desktop 与 Claude Code 的 Skill 加载机制不同，上述 Claude 路径针对 Claude Code。

### 安装与配置入口

- 跨平台安装 Skill：运行 `npx skills add AiHaoJi-Agent/aihaoji-skills -g`。它把 Skill 安装到用户级目录；Codex 和 OpenClaw 读取 `~/.agents/skills/aihaoji`，Claude Code 使用 `~/.claude/skills/aihaoji`，Hermes Agent 通过 `external_dirs` 读取共享目录。
- 配置 Key：优先由当前 Agent 校验 Key 并写入共享配置；本机已安装 `aihaoji-skills` CLI 时，可运行 `aihaoji-skills setup`。

Hermes Agent 对本仓库使用 `skills.external_dirs`。不要同时保留多个同名副本，以免宿主加载到旧版本。

## 强制规则

- 用户要查、看、找、整理 Ai好记 笔记时，必须调用开放平台接口；不要扫描本地目录、日志、缓存或源码来猜笔记内容。
- 所有内部 ID 必须来自接口返回，不能手写：`folder_id`、`target_folder_id`、`note_id`、`move_item_list[].item_id` 都必须先查询确认。
- 普通展示默认隐藏 `note_id`、`folder_id`、`user_id` 和 `key_id`；只有用户要求调试或原始字段时再展示。
- 接口报错、超时、`401/403/429/5xx` 时，明确说明当前无法通过 Ai好记开放平台获取数据，不要退回本地搜索。
- 写入前必须展示变更计划并等待用户确认；删除笔记本必须单独确认，不能包含在自动整理默认计划里。

## 参数来源

| 参数 | 来源 |
|---|---|
| `folder_id` | `GET /agent-open/api/v1/folders` 返回的真实笔记本 ID |
| `parent_id` | 新建子笔记本时来自真实父级 `folder_id`；顶层笔记本传 `parent_id=0`，不要传 `null` |
| `target_folder_id` | 单篇/批量移动笔记的目标笔记本 ID，也用于批量移动笔记本；必须来自真实笔记本 ID；移动笔记本到根目录可传 `-1` |
| `note_id` | `GET /agent-open/api/v1/notes` 或详情接口返回的真实笔记 ID |
| `move_item_list` | 与 PC 端移动接口同形：笔记 `move_type=1`，笔记本 `move_type=2`，`item_id` 为真实 ID |
| `name` | 用户明确输入，或 AI 自动归类计划生成并经用户确认 |
| `include_records` | 用户要看划线/高亮/批注/我的记录，或归类需要标注依据时传 `true` |
| `include_export_markdown` | 用户选择导出 Markdown 到本地时传 `true` |

## 常用接口

| 意图 | 接口 |
|---|---|
| 校验 Key | `GET /agent-open/api/v1/auth/verify` |
| 笔记本树 | `GET /agent-open/api/v1/folders` |
| 笔记列表 / 搜索 / 最近笔记 | `GET /agent-open/api/v1/notes` |
| 笔记详情 / 语义视图 / 导出 / 划线、批注、我的记录 | `GET /agent-open/api/v1/notes/{note_id}` |
| 新建笔记本 | `POST /agent-open/api/v1/folders` |
| 重命名笔记本 | `PUT /agent-open/api/v1/folders/{folder_id}` |
| 删除笔记本 | `DELETE /agent-open/api/v1/folders/{folder_id}` |
| 移动单篇笔记 | `PATCH /agent-open/api/v1/notes/{note_id}/folder`，请求体使用 `target_folder_id` |
| 批量移动笔记 | `POST /agent-open/api/v1/notes/batch-move` |
| 批量移动笔记本 | `POST /agent-open/api/v1/folders/batch-move` |

笔记本树读取需要 `folder:list`；写入权限通常需要 `folder:write` 或 `note:move`；记录读取需要 `note:read`。

## 意图路由

- 列出笔记本：先调 `GET /agent-open/api/v1/folders`，按接口的 `folder_tree_text` 或 `children` 真实层级展示。
- 看某个笔记本里的笔记：先用 `/folders` 定位真实 `folder_id`，再调 `/notes?folder_id=...`；不要把笔记本名复用成 `keyword`。
- 在某个笔记本里搜关键词：先定位 `folder_id`，再调 `/notes?folder_id=...&keyword=...`；结果数量以 API 返回为准，不做人为二次删减。
- 查最近/最新 N 篇：`/notes?page_no=1&page_size=N&sort_mode=create_time&sort_order=desc`；未给 N 默认 10。
- 查最早/最老 N 篇：`sort_order=asc`；未给 N 默认 10。
- 按 URL 找笔记：把完整 URL 作为 `keyword` 搜索，优先匹配返回里的真实 URL。
- 看总结/大纲/精华速览：详情接口传 `semantic_view=summary|outline|highlights`。
- 看全文/原文/润色稿：先问 `A：导出为 Markdown 文件到本地` / `B：直接在聊天里查看`；用户选 A 时用 `include_export_markdown=true`，选 B 时按 `semantic_chunk_no` 分块查看。
- 看划线/高亮/批注/我的记录：调详情接口并传 `include_records=true`；重点读取 `data.records_detail.records`、`data.records_detail.my_record`、`data.records_detail.ai_highlights` 和 `data.records_detail.ai_highlights_status`。

## 整理与写入

写入固定顺序：

1. 读取 `folders` 和 `notes`，确认真实 ID。
2. 读取详情和必要的记录信息。
3. 输出计划：将创建的笔记本、将移动的笔记/笔记本、目标位置、归类依据。
4. 等用户明确确认。
5. 创建缺失笔记本，再移动笔记或笔记本。
6. 重新查询目标笔记本或笔记列表验证结果。

新建顶层笔记本时请求体必须使用 `"parent_id": 0`。后端会把 `0` 归一为根级 `parent_id=None`；不要传 JSON `null`，线上接口可能返回“创建笔记本失败”。

自动归类整理要求：

- AI 自动归类整理必须先读笔记内容和记录依据，不能只凭标题批量移动，除非用户明确要求粗略整理。
- 已存在同名笔记本时复用，不重复创建。
- 目标不确定的笔记列为“待确认”，不要强行移动。
- 同一轮自动整理不删除笔记本。

批量移动请求优先使用 PC 端同形参数：

```json
{
  "target_folder_id": 123,
  "move_item_list": [
    {"move_type": 1, "item_id": "task_xxx", "pre_id": null}
  ]
}
```

移动笔记本时 `move_type=2`，`target_folder_id=-1` 表示移动到根目录。

## 错误处理

- `401/403`：提示 API Key 可能无效、过期、停用、删除、无权限、非会员或应用绑定失效。
- 权限不足：指出需要 `note:list`、`note:read`、`folder:list`、`folder:write` 或 `note:move`。
- `404`：说明笔记或笔记本不存在，重新查询候选让用户确认。
- `429`：说明触发频率限制，建议稍后再试或减少批量范围。

## 参考

- 详细 API、字段、记录结构、导出规则和场景话术：`references/agent-open-platform.md`
