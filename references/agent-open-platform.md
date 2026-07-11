# Ai好记 Agent Open Platform 参考

这个 skill 主要依赖开放平台的鉴权、笔记本管理、笔记列表、笔记详情、记录读取和笔记移动能力。

## 1. 校验 API Key

接口：

```http
GET /agent-open/api/v1/auth/verify
```

请求头：

```http
Authorization: sk-sxxxxxxxxxxxxxxxx
```

用途：

- 首次绑定时校验用户粘贴的 API Key
- 先判断是否是合法 API Key
- 再判断状态
- 再判断当前 API Key 对应用户是否是会员用户

成功返回重点：

- `data.valid`
- `data.user_id`
- `data.user_name`
- `data.key_id`
- `data.key_name`
- `data.key_status`
- `data.membership_active`
- `data.permissions`

## 权限约定

常用权限：

- `note:list`：读取笔记列表
- `note:read`：读取笔记详情、语义视图、划线、批注、我的记录
- `folder:list`：读取笔记本树
- `folder:write`：创建、重命名、删除和移动笔记本
- `note:move`：移动单篇或批量移动笔记

写入接口返回 `401` / `403` 时，优先提示用户检查 API Key 和应用是否具备 `folder:write` 或 `note:move`。

## 参数来源约定

Agent 不能编造内部 ID，所有写接口参数都必须来自读取接口或用户确认：

| 参数 | 来源 |
|---|---|
| `folder_id` | 来自 `GET /agent-open/api/v1/folders` 返回的真实笔记本 ID；用于列表筛选、路径参数和输出字段，不用于单篇移动请求体 |
| `parent_id` | 新建子笔记本时来自 `GET /agent-open/api/v1/folders` 返回的真实父级笔记本 ID；顶层笔记本传 `0`，不要传 `null` |
| `target_folder_id` | 来自 `GET /agent-open/api/v1/folders` 返回的真实目标笔记本 ID；单篇/批量移动笔记和批量移动笔记本请求体使用这个字段，与 PC 端 `/api/v1/folder/batch/move` 的 `BatchMoveRequest.target_folder_id` 保持一致；移动笔记本到根目录可传 `-1` |
| `note_id` | 来自 `GET /agent-open/api/v1/notes` 返回的真实笔记 ID，或详情接口解析出的真实 `note_id` |
| `move_item_list` | 与 PC 端移动接口同形；笔记使用 `move_type=1`，笔记本使用 `move_type=2`，`item_id` 必须是真实 `note_id` 或 `folder_id` |
| `name` | 用户输入或 AI 整理计划中生成并经用户确认的笔记本名 |
| `keyword` | 用户搜索词、URL、主题词或日期范围转换出的检索词 |
| `include_records` | 用户需要划线、批注、我的记录，或 AI 自动归类需要用户标注依据时传 `true` |

写入流程必须是：读取真实 ID -> 展示变更计划 -> 用户确认 -> 调用写接口 -> 再读接口验证结果。

## 2. 查询 Ai好记 笔记本树

接口：

```http
GET /agent-open/api/v1/folders
```

请求头：

```http
Authorization: sk-sxxxxxxxxxxxxxxxx
```

权限要求：

- `folder:list`

用途：

- 获取当前账号的笔记本树
- 支持先展示树，再继续查看某个笔记本里的笔记
- 每个节点包含笔记本名、创建时间、当前笔记本笔记数、children

返回重点：

- `data.total`
- `data.folders[].folder_id`
- `data.folders[].folder_name`
- `data.folders[].parent_id`
- `data.folders[].create_time`
- `data.folders[].note_count`
- `data.folders[].children`
- `data.folder_tree_text`

展示约束：

- 默认不要向用户展示 `folder_id`
- 对用户展示时统一称为“笔记本”，但用户说“文件夹”也视为同义触发
- 如果接口返回了 `data.folder_tree_text`，优先直接原样使用该字段
- 不要改写 `folder_tree_text` 的格式
- 不要补编号
- 不要生成 `1 / 1.1 / 1.1.1`
- 不要补“当前可见结构视图”“近似树”“根目录”这类说明
- 只有在用户明确要求原始 JSON / 调试信息时，才展开 `folders`
- 如果接口返回了 `children` 或 `parent_id`，必须按真实层级展示
- 不允许声称“接口没有树状字段”或自行编造“近似树”“可见结构视图”

## 2.1 创建 Ai好记 笔记本

接口：

```http
POST /agent-open/api/v1/folders
```

权限要求：

- `folder:write`

请求体：

```json
{
  "name": "产品研究",
  "parent_id": 0
}
```

说明：

- 创建顶层笔记本时传 `parent_id=0`；后端会归一为根级 `parent_id=None`
- 创建子笔记本时，`parent_id` 必须来自 `/folders` 返回的真实父级 `folder_id`
- 不要传 JSON `null` 创建顶层笔记本；线上接口可能返回“创建笔记本失败”
- 创建前应先调用 `GET /agent-open/api/v1/folders` 检查同级是否已有同名笔记本
- 返回重点：`data.folder_id`、`data.folder_name`、`data.parent_id`

## 2.2 重命名 Ai好记 笔记本

接口：

```http
PUT /agent-open/api/v1/folders/{folder_id}
```

权限要求：

- `folder:write`

请求体：

```json
{
  "name": "增长研究"
}
```

说明：

- 重命名前必须先从笔记本树定位真实 `folder_id`
- 默认笔记本可能被后端拒绝重命名，skill 应透传错误语义

## 2.3 删除 Ai好记 笔记本

接口：

```http
DELETE /agent-open/api/v1/folders/{folder_id}
```

权限要求：

- `folder:write`

说明：

- 删除前必须单独向用户确认
- 不允许在“AI 自动归类整理”流程里默认删除笔记本
- 如果后端因为默认笔记本、处理中任务、权限或业务规则拒绝删除，skill 应透传错误语义

## 2.4 批量移动 Ai好记 笔记本

接口：

```http
POST /agent-open/api/v1/folders/batch-move
```

权限要求：

- `folder:write`

请求体：

```json
{
  "target_folder_id": 123,
  "move_item_list": [
    {"move_type": 2, "item_id": "456", "pre_id": null}
  ]
}
```

说明：

- 字段与 PC 端 `/api/v1/folder/batch/move` 保持同形
- `move_type=2` 表示移动笔记本
- `target_folder_id=-1` 表示移动到根目录
- `pre_id` 可为空；需要指定排序位置时传同级前一个笔记本 ID
- 移动前必须确认 `item_id` 和 `target_folder_id` 都来自 `/folders` 返回

## 3. 搜索 Ai好记内容列表

接口：

```http
GET /agent-open/api/v1/notes
```

查询参数：

- `page_no`
- `page_size`
- `keyword`
- `folder_id`
- `sort_mode`
- `sort_order`

请求头：

```http
Authorization: sk-sxxxxxxxxxxxxxxxx
```

权限要求：

- `note:list`

用途：

- 通过关键词找到候选 Ai好记内容
- 用户不知道 `note_id` 时，必须先走这一步
- 支持按创建时间查最新 / 最老笔记
- 支持按 URL 检索对应笔记

补充说明：

- `sort_mode=create_time&sort_order=desc`：最新内容
- `sort_mode=create_time&sort_order=asc`：最老内容
- `keyword=<完整 URL>`：按链接找笔记
- `folder_id=<笔记本 ID>`：按笔记本筛选笔记

展示约束：

- 默认不要向用户展示 `note_id`
- 默认不要向用户展示 `folder_id`
- 用“第 1 篇 / 第 2 篇”这类自然编号展示候选笔记
- 如果是按 `folder_id` 查询结果，不允许把不在该笔记本里的笔记混进来

## 4. 查询 Ai好记详情

接口：

```http
GET /agent-open/api/v1/notes/{note_id}
```

查询参数：

- `page_no`
- `page_size`
- `start_time_str`
- `end_time_str`
- `semantic_view`
- `semantic_chunk_no`
- `semantic_chunk_size`
- `include_export_markdown`
- `include_records`

请求头：

```http
Authorization: sk-sxxxxxxxxxxxxxxxx
```

权限要求：

- `note:read`

返回重点：

- `data.meta`
- `data.sections`
- `data.available_views`
- `data.semantic_view`
- `data.semantic_markdown`
- `data.semantic_available`
- `data.semantic_message`
- `data.export_markdown`
- `data.meta.my_record`
- `data.records_detail`

## 4.1 通过详情查询划线、批注、我的记录

查询方式：

```http
GET /agent-open/api/v1/notes/{note_id}?include_records=true
```

说明：记录能力统一走笔记详情接口，避免让 Agent 在“查看详情”和“读取记录”之间选择两套入口。

权限要求：

- `note:read`

用途：

- 读取用户对单篇笔记做过的划线、高亮、批注记录
- 读取文章级“我的记录”内容
- 给 AI 自动归类整理提供用户意图上下文

返回重点：

- `data.records_detail.note_id`
- `data.records_detail.records[].record_id`
- `data.records_detail.records[].selected_text`
- `data.records_detail.records[].record_context[]`
- `data.records_detail.records[].create_time`
- `data.records_detail.my_record`
- `data.records_detail.ai_highlights`
- `data.records_detail.ai_highlights_status`

展示约束：

- 默认不要展示内部 `record_id`
- 面向用户时按“选中文本 / 批注内容 / 所在段落 / 创建时间”整理
- 如果记录用于归类依据，可以摘要说明“依据批注/划线判断”，但不要输出整段原始 JSON

## 5. 移动单篇笔记到指定笔记本

接口：

```http
PATCH /agent-open/api/v1/notes/{note_id}/folder
```

权限要求：

- `note:move`

请求体：

```json
{
  "target_folder_id": 123
}
```

说明：

- 移动前必须先用 `GET /agent-open/api/v1/folders` 定位真实目标笔记本 ID，并作为 `target_folder_id` 传入
- 移动前必须先用 `GET /agent-open/api/v1/notes` 或上下文确认真实 `note_id`
- 返回重点：`data.note_id`、`data.folder_id`、`data.folder_name`

## 5.1 批量移动笔记

接口：

```http
POST /agent-open/api/v1/notes/batch-move
```

权限要求：

- `note:move`

请求体：

```json
{
  "target_folder_id": 123,
  "move_item_list": [
    {"move_type": 1, "item_id": "task_xxx", "pre_id": null},
    {"move_type": 1, "item_id": "task_yyy", "pre_id": null}
  ]
}
```

说明：

- 批量移动前必须先向用户展示移动计划
- `target_folder_id` 必须来自 `GET /agent-open/api/v1/folders` 返回的真实目标笔记本 ID
- `move_item_list[].item_id` 必须来自接口返回的真实 `note_id`，不允许编造
- 字段名使用 `target_folder_id` 和 `move_item_list`，不要改成 `folder_id`；这是为了和 PC 端批量移动请求保持一致
- 兼容旧字段 `note_ids`，但新文档和新调用优先使用 `move_item_list`
- 完成后建议调用 `GET /agent-open/api/v1/notes?folder_id=123` 验证结果

## 6. AI 自动归类整理推荐流程

1. `GET /agent-open/api/v1/folders` 获取已有笔记本
2. `GET /agent-open/api/v1/notes` 获取待整理笔记
3. `GET /agent-open/api/v1/notes/{note_id}` 读取标题、摘要、大纲、语义内容
4. `GET /agent-open/api/v1/notes/{note_id}?include_records=true` 读取划线、批注、我的记录
5. 生成整理计划，列出将创建的笔记本和将移动的笔记
6. 用户确认后，用 `POST /agent-open/api/v1/folders` 创建缺失笔记本
7. 用 `PATCH /agent-open/api/v1/notes/{note_id}/folder` 或 `POST /agent-open/api/v1/notes/batch-move` 移动笔记；单篇移动传 `target_folder_id`，批量移动传 `target_folder_id + move_item_list`
8. 重新查询笔记本或目标笔记列表做校验

安全约束：

- 自动整理不得静默写入，必须先展示计划
- 自动整理不得默认删除笔记本
- 不确定分类的笔记应列为“待确认”，不要强行移动

## semantic_view 说明

可选值：

- `summary`
- `highlights`
- `outline`
- `polish`
- `original`
- `full`

建议使用：

- 用户说“看总结” -> `summary`
- 用户说“看精华速览” -> `highlights`
- 用户说“看大纲” -> `outline`
- 用户说“看润色” -> `polish`
- 用户说“看原文” -> `original`
- 用户说“看全部” -> `full`

## include_export_markdown 说明

可选值：

- `true`
- `false`

建议使用：

- 用户说“查看详情 / 看详情 / 打开详情 / 看这篇笔记”时，不要默认直接返回概览；应先让用户选择：
  - 导出 Markdown 到本地
  - 直接在聊天里查看
- 用户说“看全文 / 看原文 / 看润色稿”时，也不要默认直接把长内容发在聊天里；这三类长内容与 `full` 一样，应先让用户选择：
  - 导出 Markdown 到本地
  - 直接在聊天里查看
- 只有用户明确说“看总结 / 看大纲 / 看精华速览”时，才可直接按短视图请求处理
- 如果用户选择“导出 Markdown 到本地”，调用详情接口时必须显式带上：

```http
GET /agent-open/api/v1/notes/{note_id}?include_export_markdown=true
```

- 如果用户同时明确指定了某个语义视图，例如 `summary / outline / highlights / polish / original / full`，则按所选视图一起传参，例如：

```http
GET /agent-open/api/v1/notes/{note_id}?semantic_view=full&include_export_markdown=true
```

- 导出本地 `.md` 时，优先直接使用 `data.export_markdown` 原样写入文件，不要自己重拼标题、不要补第二个重复标题、不要把多个视图混在同一份导出里
- 如果当前响应没有返回 `data.export_markdown`，要明确告知用户当前接口未返回导出内容，而不是假装已经完成 Markdown 导出

## 推荐调用流程

### 场景 A：用户不知道 note_id

1. 先搜索：

```http
GET /agent-open/api/v1/notes?keyword=Ai好记 后台数据
```

2. 拿到候选结果后，根据标题、时间、摘要选出最佳 Ai好记内容
3. 再读取详情：

```http
GET /agent-open/api/v1/notes/{note_id}?semantic_view=summary
```

### 场景 B：用户已经明确指定某篇

如果上一轮已经拿到了 `note_id`，就直接调详情接口。

补充交互约束：

- 如果用户意图是“查看详情 / 看详情 / 打开详情 / 看这篇笔记”，不要把它直接等价成“先给 summary / outline / full 的概览”
- 如果用户意图是“看全文 / 看原文 / 看润色稿”，也不要绕过询问直接发长内容；这三类请求与 `full` 一样，先进入“查看方式选择”流程：
  - A：导出 Markdown 到本地
  - B：直接在聊天里查看
- 只有当用户明确指定“看总结 / 看大纲 / 看精华速览”时，才直接视为对应短视图请求
- 对于 `full / original / polish`，在用户选择 `B` 后，再进入对应长视图的聊天分块链路
- 也就是说：
  - “看这篇笔记” ≠ 默认看 `summary`
  - “查看详情” ≠ 默认先给详情概览
  - “打开详情” ≠ 默认展开正文
  - “看全文” ≠ 默认直接展开 `full`
  - “看原文” ≠ 默认直接展开 `original`
  - “看润色稿” ≠ 默认直接展开 `polish`
- 当用户选择 A 时，详情接口必须显式携带 `include_export_markdown=true`

### 场景 C：用户要看笔记本树

```http
GET /agent-open/api/v1/folders
```

处理要求：

1. 先返回树状层级
2. 默认不展示 `folder_id`
3. 每个节点展示名称、笔记数量、创建时间
4. 如果用户点名某个笔记本，再继续查该笔记本里的笔记

### 场景 D：用户要看某个笔记本里的笔记

```http
GET /agent-open/api/v1/notes?page_no=1&page_size=10&folder_id=123
```

处理要求：

1. 如果用户说的是笔记本名，必须先从 `/folders` 结果里定位
2. 如果用户说的是树中的自然顺序或“第 1 个笔记本”，按当前会话里的树节点映射到真实节点
3. 拿到真实 `folder_id` 后，再调用 `GET /notes?...&folder_id=...`
4. 返回笔记列表时默认不展示 `note_id`
5. 默认把“笔记本名称 / 创建时间 / 文件数 / 当前页笔记列表”一起展示
6. 如果总数超过一页，要保留分页语义，支持继续看下一页

强制约束：

- 用户说“看一下Ai好记的笔记本”或“看一下Ai好记笔记本下的笔记”时，必须先查 `/folders`
- 必须先定位 `Ai好记` 对应的 `folder_id`
- 然后再调用 `GET /notes?...&folder_id=...`
- 这里的 `Ai好记` 是 `folder_name`，不是 `keyword`
- 一旦进入这条链路，`/notes` 请求必须视为 `keyword=None`
- 不允许把这个需求降级成 `keyword=Ai好记` 的关键词搜索
- 不允许把用于定位笔记本的 `folder_name=Ai好记` 继续复用成 `keyword=Ai好记`
- 不允许把关键词候选列表当成“当前笔记本下的所有笔记”
- 不允许把别的笔记本里的笔记混进当前笔记本列表

### 场景 D2：用户要在某个笔记本里搜索相关笔记

```http
GET /agent-open/api/v1/notes?page_no=1&page_size=10&folder_id=123&keyword=Ai好记
```

处理要求：

1. 必须先从 `/folders` 里定位真实 `folder_id`
2. 用户句子里用于定位笔记本的名字视为 `folder_name`
3. 用户句子里“关于 / 相关于 / 搜 / 找 / 提到”的对象才视为 `keyword`
4. 返回时必须明确这是“该笔记本内命中关键词的结果”
5. 结果数量必须以 `GET /notes?...&folder_id=...&keyword=...` 的 API 返回为准
6. 不允许再额外套用“标题严格命中”“讲这个团队本身”之类更窄的人为语义筛选
7. 不允许在 API 返回结果之上再做任何收紧结果集的人为二次筛选；接口返回什么，就展示什么
8. 如果用户后续要看某一条，再从这批 API 原始返回结果中继续查看详情

强制约束：

- 只有用户明确表达“在某个笔记本里找/搜/筛和某关键词相关的笔记”时，才允许同时传 `folder_id + keyword`
- 如果用户只是说“看一下Ai好记笔记本下的笔记”，必须视为整本浏览，不能补 `keyword`
- `folder_name` 只负责定位笔记本，`keyword` 只负责笔记本内搜索，二者不能因为文本相同就自动复用
- 如果 API 返回 5 篇，就展示 5 篇；不允许自行缩成 2 篇
- 不允许把“更相关”“更像在讲这个团队本身”“标题更明确”当作缩减返回结果的理由

### 场景 E：用户要看最近 N 篇

```http
GET /agent-open/api/v1/notes?page_no=1&page_size=N&sort_mode=create_time&sort_order=desc
```

说明：`N` 取用户在问题里给出的数量；如果用户没说，默认可取 `10`。

### 场景 F：用户要看最老 N 篇

```http
GET /agent-open/api/v1/notes?page_no=1&page_size=N&sort_mode=create_time&sort_order=asc
```

说明：`N` 取用户在问题里给出的数量；如果用户没说，默认可取 `10`。

### 场景 G：用户按 URL 找笔记

```http
GET /agent-open/api/v1/notes?page_no=1&page_size=10&keyword=https%3A%2F%2Fwww.bilibili.com%2Fvideo%2FBV...
```

## 配置建议

优先使用共享配置文件：

```text
~/.aihaoji/config.json
```

格式示例：

```json
{
  "provider": "aihaoji",
  "apiKey": "sk-sxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "baseUrl": "https://openapi.aihaoji.com",
  "userId": "user_xxx",
  "userName": "张三",
  "keyId": "agent_open_key_xxx",
  "keyName": "默认密钥"
}
```

## 当前边界

这个 skill 当前不涉及：

- API Key 自动申请
- 开放平台自动注册
- OAuth 回调授权

它只负责：

- 用已有 API Key 读你的笔记和用户记录
- 完成“校验 -> 笔记本 / 搜索 -> 详情 / 记录 / 整理写入”的调用链
- 在用户确认后创建笔记本、移动笔记、移动笔记本和批量移动笔记
- 通过共享配置让 OpenClaw、Codex、Claude 共用同一份 Ai好记配置

## 详情查看规则

如果用户说“查看详情 / 看详情 / 打开详情 / 看这篇笔记”，要先分流成：

- `A`：导出 Markdown 到本地
- `B`：直接在聊天里查看

约束：

- 用户没有明确回答 `A` 或 `B` 前，第一条回复必须只问 `A` 或 `B`
- 用户没有明确回答 `A` 或 `B` 前，不允许输出详情概览、正文、引用摘录，或 `summary / outline / highlights / full / polish / original` 的任何内容
- `A` 路线必须调用 `GET /agent-open/api/v1/notes/{note_id}`，并显式带上 `include_export_markdown=true`
- 如果用户明确指定视图，再追加 `semantic_view=<view>`
- `A` 路线只允许把接口返回的 `data.export_markdown` 原样写入本地 `.md`，不允许自己重新拼标题，也不允许把多个不相关视图混进同一文件
- `B` 路线里，`summary`、`outline`、`highlights` 可以一次性返回
- `full`、`polish`、`original` 在聊天里必须带 `semantic_view`
- 第一次查看 `full`、`polish`、`original` 时，必须从 `semantic_chunk_no=1` 开始
- 每次回复只能使用当前请求返回的 `data.semantic_markdown`
- 用户回复“继续”后，才允许把 `semantic_chunk_no` 加 1 再请求下一块
- 导出 `.md` 时不要分块，直接使用 `data.export_markdown`
- `full`、`polish`、`original` 的聊天分块里，只允许输出当前视图的当前 chunk
- 不允许在 `full` 的 chunk 回复里混入 `summary`、`outline`、`highlights` 或自定义总结

## 鉴权异常处理约定

当校验接口、列表接口或详情接口返回 `401` / `403` 时，优先按后端明确错误语义处理。

skill 侧需要明确提示用户以下可能性：

- 粘贴的内容不是合法 API Key
- API Key 已过期
- API Key 已停用
- API Key 已删除
- 当前 API Key 对应用户不是会员用户
- API Key 缺少 `note:list`、`note:read`、`folder:list`、`folder:write` 或 `note:move`
- API Key 对应应用、用户绑定或授权关系失效

不允许只说“请求失败”或“接口异常”。

推荐提示文案：

```text
当前 Ai好记 API Key 已不可用，可能是已过期、已停用、已删除，或没有当前接口权限。
请检查开放平台里的 Key 状态、权限范围和应用绑定关系。
```

如果后端明确返回“当前 API Key 对应用户不是会员用户”，优先透传该提示，不要改写成泛化错误。
