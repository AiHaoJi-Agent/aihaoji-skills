---
name: Ai好记
description: |
  AI好记笔记查询 skill，专门用于搜索和读取 AI好记里的笔记、笔记本和详情内容。

  触发这些请求时优先使用：
  - “看 Ai好记 笔记本”
  - “看某个笔记本里的笔记”
  - “看某个文件夹下的笔记”
  - “看某个笔记本里的笔记”
  - “查 Ai好记 笔记”
  - “搜笔记”
  - “看笔记”
  - “最近 10 篇笔记”
  - “最老 5 篇笔记”
  - “找Ai好记相关的笔记”
  - “按 URL 找笔记”
  - “看这篇笔记的总结/大纲/精华速览/润色稿/原文”

  只使用三个开放平台接口：
  - GET /agent-open/api/v1/folders
  - GET /agent-open/api/v1/notes
  - GET /agent-open/api/v1/notes/{note_id}

metadata: {"openclaw": {"requires": {}, "optionalEnv": ["AIHAOJI_API_KEY"], "baseUrl": "https://openapi.readlecture.cn", "homepage": "https://openapi.readlecture.cn"}}
---

# Ai好记 Agent Open Skill

## 配置来源

优先级如下：

1. `~/.aihaoji/config.json`
2. `$AIHAOJI_API_KEY`
3. `$AIHAOJI_BASE_URL`

推荐优先使用共享配置文件：

```text
~/.aihaoji/config.json
```

格式示例：

```json
{
  "provider": "aihaoji",
  "apiKey": "sk-sxxxxxxxx",
  "baseUrl": "https://openapi.readlecture.cn",
  "userId": "user_xxx",
  "userName": "张三",
  "keyId": "agent_open_key_xxx",
  "keyName": "默认密钥"
}
```

`npx aihaoji-openclaw setup` 会自动写这份文件。OpenClaw、Codex、Claude 这类通过 skill 使用 Ai好记 的场景，优先从这里读取，不要求用户自己设置环境变量。

## 鉴权规则

请求头统一使用：

```text
Authorization: $AIHAOJI_API_KEY
```

当前 API Key 形态：

```text
sk-s...
```

## 当前开放能力

- 获取 AI好记笔记本树
- 搜索 AI好记内容列表
- 按笔记本读取笔记列表
- 读取单篇 AI好记详情
- 读取单篇 AI好记内容的语义视图

当前不开放：

- 创建
- 更新
- 删除

如果用户要求写入能力，直接说明当前 skill 只支持只读。

## 首次使用前检查

每次调用前，先检查：

1. `~/.aihaoji/config.json` 是否存在且包含 `apiKey`
2. 如果共享配置不存在，再看 `$AIHAOJI_API_KEY` 是否存在
3. `baseUrl` 默认使用 `https://openapi.readlecture.cn`

如果用户还没有安装 skill，优先建议先运行：

```bash
npx skills add AiHaoJi-Agent/aihaoji-skills
```

如果当前没有 API Key，不要先让用户理解 `setup` 命令，优先直接走聊天内绑定流程：

1. 告诉用户先去开发者密钥页面创建 API Key：

```text
https://openapi.readlecture.cn/zh/keys
```

2. 提示用户创建完成后，直接把 `sk-s...` 粘贴回来
3. 拿用户粘贴的 key 调用：

```http
GET /auth/verify
Authorization: 用户粘贴的 sk-s...
```

4. 如果校验通过，再写入本地配置

这里的“本地配置”优先指：

```text
~/.aihaoji/config.json
```

如果宿主支持，再同步写入宿主自己的配置文件。

推荐引导话术：

```text
当前还没有配置 Ai好记 API Key。
请先前往以下地址创建开发者密钥：
https://openapi.readlecture.cn/zh/keys

创建完成后，把你的 API Key 粘贴给我，我会先帮你校验；校验通过后再自动完成本地配置。
```

如果自动写入本地配置失败，再退回备用命令：

```bash
npx aihaoji-openclaw setup
```

## 使用规则

## 强制执行规则

只要用户是在“查 Ai好记 笔记 / 看 Ai好记 笔记 / 找 Ai好记 笔记”，就必须优先调用 AI好记开放平台接口。

禁止把下面这些动作当成主查询手段：

- 扫描本地目录
- 搜索本地日志
- 搜索本地缓存
- 搜索源码仓库
- 根据磁盘文件自行猜测用户笔记内容

也就是说，不允许出现这类行为：

- 先搜 `~/.aihaoji`
- 先搜 `~/.pm2/logs`
- 先扫本地项目目录
- 用“本地没搜到”代替“AI好记里没有”

正确顺序必须是：

1. 读取本地配置，只用于拿到 `apiKey` 和 `baseUrl`
2. 直接调用 AI好记开放平台接口
3. 根据接口结果生成回答

如果接口报错、超时、401、403、5xx，应该明确告诉用户“当前无法通过 AI好记开放平台获取数据”，而不是退回去扫本地磁盘。

### 0. 触发优先级

以下情况，优先调用 Ai好记 skill：

1. 用户话里明确出现：
   - `Ai好记`
2. 用户表达的是查找或查看笔记类需求，例如：
   - `查笔记`
   - `搜笔记`
   - `看笔记`
   - `找我的笔记`
   - `打开这条笔记`

如果用户没有明确指定别的知识源、别的系统或别的产品，且语义上是在“找笔记 / 看笔记”，默认理解为去 Ai好记 里查。

### 1. 查列表时

对用户展示时，统一称为“笔记本”。
如果用户说“文件夹”或“笔记本”，都按同一能力处理。

如果用户是在问：

- `文件夹`
- `笔记本`
- `文件夹列表`
- `我的文件夹`
- `Ai好记 文件夹里的笔记`
- `Ai好记 笔记本里的笔记`
- `看一下Ai好记的文件夹`
- `看一下Ai好记文件夹下的笔记`

优先使用笔记本接口：

```http
GET /folders
Authorization: $AIHAOJI_API_KEY
```

如果用户已经明确指定某个笔记本，再使用：

```http
GET /notes?page_no=1&page_size=10&folder_id=123
Authorization: $AIHAOJI_API_KEY
```

只有用户明确表达“在某个笔记本里找/搜/筛和某关键词相关的笔记”时，才允许使用：

```http
GET /notes?page_no=1&page_size=10&folder_id=123&keyword=Ai好记
Authorization: $AIHAOJI_API_KEY
```

处理要求：

1. 必须先从 `/folders` 里定位真实 `folder_id`
2. 用户句子里用于定位笔记本的名字视为 `folder_name`
3. 用户句子里“关于 / 相关于 / 搜 / 找 / 提到”的对象才视为 `keyword`
4. 返回时必须明确这是“该笔记本内命中关键词的结果”
5. 结果数量必须以 `GET /notes?...&folder_id=...&keyword=...` 的 API 返回为准
6. 不允许再额外套用“标题严格命中”“讲这个团队本身”之类更窄的人为语义筛选
7. 不允许在 API 返回结果之上再做任何收紧结果集的人为二次筛选；接口返回什么，就展示什么
8. 如果 API 返回 5 篇，就展示 5 篇；不允许自行缩成 2 篇

分页规则：

- 默认 `page_no=1`
- 默认 `page_size=10`
- 如果用户明确说“前 3 篇 / 前 5 篇 / 前 20 篇”，把数量映射到 `page_size`
- 如果用户说“下一页 / 再看后 10 篇 / 第 2 页”，继续递增 `page_no`
- 这条链路的目标是“当前笔记本下的全部笔记的分页列表”，不是关键词候选搜索
- 只有在用户明确说“关于 / 相关于 / 搜 / 找 / 筛”时，才允许切换成“当前笔记本内关键词搜索”

如果用户明确是在“全量笔记”里搜索关键词，调用：

```http
GET /notes?page_no=1&page_size=10&keyword=Ai好记
Authorization: $AIHAOJI_API_KEY
```

如果用户明确说“最近”“最新”“刚刚”的笔记，按创建时间倒序查询。

如果用户还明确给了数量，例如：

- `最新 5 篇`
- `最近 10 篇`
- `最近二十篇`

就把用户说的数量映射到 `page_size`；如果没有明确数量，默认取 `10`。

调用：

```http
GET /notes?page_no=1&page_size=10&sort_mode=create_time&sort_order=desc
Authorization: $AIHAOJI_API_KEY
```

如果用户明确说“最老”“最早”的笔记，按创建时间正序查询。

如果用户还明确给了数量，例如：

- `最老 5 篇`
- `最早 10 篇`
- `最老二十篇`

就把用户说的数量映射到 `page_size`；如果没有明确数量，默认取 `10`。

调用：

```http
GET /notes?page_no=1&page_size=10&sort_mode=create_time&sort_order=asc
Authorization: $AIHAOJI_API_KEY
```

如果用户给的是完整 URL，直接把 URL 当作 `keyword` 去检索：

```http
GET /notes?page_no=1&page_size=10&keyword=https%3A%2F%2Fwww.bilibili.com%2Fvideo%2FBV...
Authorization: $AIHAOJI_API_KEY
```

返回重点字段：

- `data.folders[].folder_id`
- `data.folders[].folder_name`
- `data.folders[].create_time`
- `data.folders[].note_count`
- `data.folders[].children`
- `data.folder_tree_text`
- `data.total`
- `data.notes[].note_id`
- `data.notes[].title`
- `data.notes[].folder_name`
- `data.notes[].create_time`

对用户展示时：

- 默认不要展示 `note_id`
- 默认不要展示 `folder_id`
- 列表里优先展示“第 1 篇 / 第 2 篇 / 第 3 篇”这类自然编号
- 同时展示标题、创建时间、所属文件夹、来源
- 只有用户明确要求“显示 note_id / 接口原始字段 / 调试信息”时，才显示 `note_id`

当用户说“看一下Ai好记的文件夹”和“看一下Ai好记文件夹下的笔记”时，强制执行下面的固定流程：

1. 先调用 `GET /folders`
2. 在返回的笔记本树里定位名称为 `Ai好记` 的节点
3. 读取该节点的真实 `folder_id`
4. 再调用 `GET /notes?page_no=1&page_size=10&folder_id=<该 folder_id>`
   这一步里 `Ai好记` 只是 `folder_name`，不是 `keyword`
   这一跳必须显式视为 `keyword=None`
5. 把“当前笔记本信息 + 当前页笔记列表 + 如有更多页可继续翻页”一起展示给用户

禁止行为：

- 不允许把“Ai好记文件夹下的笔记”改写成 `keyword=Ai好记` 的关键词搜索
- 不允许把用于定位笔记本的 `folder_name=Ai好记` 继续复用成 `keyword=Ai好记`
- 不允许只返回标题里碰巧命中的 1 篇候选
- 不允许跳过 `/folders` 直接假设 `folder_id`
- 不允许把“相关笔记搜索结果”伪装成“当前笔记本下的全部笔记”
- 不允许把别的笔记本里的笔记混进当前笔记本列表
- 不允许一边说“这个笔记本有 9 篇”，一边只展示 `keyword=Ai好记` 命中的 5 篇还声称这是整本结果

默认展示格式：

```text
笔记本：Ai好记
创建时间：2025-08-06
文件数：9

第 1 篇：首次公开！Ai好记的后台数据长啥样？
  所属笔记本：Ai好记
  创建时间：2025-07-02

第 2 篇：1秒能拍44万帧？！高速摄影的代价是…
  所属笔记本：Ai好记
  创建时间：未知
```

如果返回的是笔记本树，必须用层级渐进式列表展示，不要平铺成长 JSON，也不要一次性把所有层级揉成一句话。

如果接口已经返回 `data.folder_tree_text`：

- 默认直接使用 `data.folder_tree_text`
- 不要重写格式
- 不要补编号
- 不要改成 `1 / 1.1 / 1.1.1`
- 不要补“根目录”“当前可见结构视图”“近似树”这类解释
- 不要自己重新推导父子关系
- 只有用户明确要求“原始 JSON / 原始字段 / 调试信息”时，才展开 `folders` 原始结构

禁止行为：

- 不允许声称“接口没有父子层级字段”或“只能推测树状结构”，除非接口实际缺失 `children` / `parent_id`
- 不允许自己编造“根目录 / 可见结构视图 / 伪树 / 近似树”
- 如果 `/folders` 已返回 `children` 或 `parent_id`，必须按接口真实层级展示
- 不允许把扁平列表重新猜成一棵树再告诉用户这是接口结果

推荐展示格式：

```text
默认笔记本 创建时间：2025-05-06 文件数：210
    Ai好记 创建时间：2025-08-06 文件数：9
    3123131 创建时间：2025-08-20 文件数：0
        3214 创建时间：2025-05-08 文件数：0
        21312qweqweq 创建时间：2025-08-20 文件数：2
玉米太 创建时间：2025-06-27 文件数：9
发布会 创建时间：2025-09-16 文件数：5
```

列表展示规则：

- 只展示 `笔记本名 / 当前笔记本笔记数 / 创建时间`
- 子笔记本必须缩进
- 不使用任何编号
- 默认最多先展示 3 层
- 如果顶层很多，先展示全部顶层和命中的相关分支
- 如果用户指定了某个笔记本，例如“Ai好记”，优先展开该分支
- 不向普通用户展示 `folder_id`
- 如果某个节点的 `parent_id` 指向不存在的父节点，把它当成顶层节点展示

如果用户说：

- `列出笔记本`
- `看笔记本树`
- `Ai好记 笔记本`

回答时先给笔记本列表，再继续询问是否查看该笔记本里的笔记。

如果 `/folders` 返回里已经存在用户点名的笔记本，例如 `Ai好记`，优先直接展开该节点所在分支，而不是改写成“当前可见结构视图”。

### 2. 查详情时

必须先拿到明确的 `note_id`。

调用：

```http
GET /notes/{note_id}?semantic_view=summary
Authorization: $AIHAOJI_API_KEY
```

支持的 `semantic_view`：

- `summary`
- `highlights`
- `outline`
- `polish`
- `original`
- `full`

补充强制规则：

- 当用户说“查看详情 / 看详情 / 打开详情 / 看这篇笔记”时，不允许默认先返回详情概览，也不允许先输出 `summary / outline / highlights / polish / original / full` 的任何内容
- 当用户明确说“看全文 / 看原文 / 看润色稿”时，也不要默认直接在聊天里展开正文；这三类长内容请求与 `full` 一样，必须先进入查看方式选择流程
- 这类请求的第一条回复只能是查看方式选择：
  - `A：导出为 Markdown 文件到本地`
  - `B：直接在聊天里查看`
- 只有用户明确选择 `A` 后，才允许进入 Markdown 导出链路
- 只有用户明确选择 `B` 后，才允许继续返回详情概览或指定视图内容
- 只有用户明确说“看总结 / 看大纲 / 看精华速览”这类短视图型指令时，才允许直接走对应 `semantic_view`
- 也就是说：
  - “看这篇笔记” ≠ 默认看 `summary`
  - “查看详情” ≠ 默认先给详情概览
  - “打开详情” ≠ 默认展开正文
  - “看全文” ≠ 默认直接展开 `full`
  - “看原文” ≠ 默认直接展开 `original`
  - “看润色稿” ≠ 默认直接展开 `polish`
- 当用户选择 `A` 时，必须显式携带 `include_export_markdown=true`
- 当接口返回 `data.export_markdown` 时，导出文件必须直接使用该字段原样写入，不允许重新拼标题、补第二个重复标题，或把多个视图混进同一个 `.md`

### 3. 用户不知道 note_id 时

不允许直接编造 `note_id`。

正确流程：

1. 先用用户问题生成搜索词
2. 调 `GET /notes?keyword=...`
3. 对候选结果做简单匹配
4. 选出最合适的一条
5. 再调详情接口

例如用户说：

```text
查一下本文通过Ai好记十年运营数据的深度分析，揭示了内容创作中爆款视频的关键作用...
```

应先搜索：

```text
Ai好记 十年 运营数据 爆款视频 平台算法 数据指标
```

然后从结果中选中：

```text
首次公开！Ai好记的后台数据长啥样？
```

如果用户是按 URL 查找，匹配优先级应为：

1. `data.notes[].url` 与用户提供 URL 完全一致
2. 去掉追踪参数后主 URL 一致
3. 标题与 URL 检索结果同时匹配
4. 如果仍有多条候选，先把候选列表展示给用户，再让用户确认

只要已经精确命中单条 URL，不需要再让用户补充 `note_id`。

### 4. 回复格式建议

如果用户要的是正文类内容，优先用这种格式输出：

```md
# {{title}}

- 创建时间：{{create_time}}
- 所属笔记本：{{folder_name}}

## {{semantic_title}}

{{semantic_markdown}}
```

默认不要向用户展示：

```md
- note_id：{{note_id}}
```

同理，默认不要展示：

```md
- folder_id：{{folder_id}}
```

## 场景化回复要求

以下场景优先按这些话术风格执行；如果当前已经能覆盖该能力，则保持能力不变，只把回复口径对齐到这里。

### 场景 1：最近的笔记

用户说：

```text
帮我看一下我最近的笔记。
```

处理规则：

- 默认理解为按创建时间倒序查询
- 默认取最近 `10` 篇
- 调用 `GET /notes?page_no=1&page_size=10&sort_mode=create_time&sort_order=desc`

推荐回复：

```text
我帮你整理了最近的笔记，按时间倒序展示，你可以继续说“打开第 2 篇”或“看第一篇的总结”。
```

### 场景 2：按主题找相关内容

用户说：

```text
帮我找Ai好记相关的内容。
```

处理规则：

- 使用主题词调用 `GET /notes?keyword=...`
- 结果以接口返回为准，按接口返回顺序或接口排序字段展示
- 返回候选列表时，优先展示标题、创建时间、所属笔记本
- 候选列表默认不要展示 `note_id`
- 不允许在接口返回结果上再做人为二次删减或额外相关性解释

推荐回复：

```text
我找到几篇和“Ai好记”相关的笔记，先按接口返回结果整理给你。
```

### 场景 3：按标题定位某一篇

用户说：

```text
帮我看 XXX 这篇笔记。
```

处理规则：

- 先搜索候选，不允许直接假设 `note_id`
- 如果只有一篇高置信匹配，直接打开
- 如果有多篇相似结果，先返回候选列表让用户确认

推荐回复：

```text
我先帮你定位这篇笔记；如果只有一篇匹配，就直接打开；如果有多篇相似结果，会先给你候选列表确认。
```

### 场景 4：看这篇笔记 / 看全文 / 看原文 / 看润色稿

用户说：

```text
帮我看这篇笔记。
看这篇笔记的全文。
看这篇笔记的原文。
看这篇笔记的润色稿。
```

处理规则：

- 如果上下文里已经明确当前笔记，且用户意图是“查看详情 / 看详情 / 打开详情 / 看这篇笔记 / 看全文 / 看原文 / 看润色稿”，第一条回复只能给出 `A / B` 选择，不允许先给详情概览，也不允许直接开始发长内容。
- `A`：导出 Markdown 到本地
  - 先调用 `GET /notes/{note_id}`；如果用户明确指定 `full / polish / original / summary / outline / highlights` 之一，再带上对应的 `semantic_view`
  - 必须显式携带 `include_export_markdown=true`
  - 只允许把接口返回的 `data.export_markdown` 原样写入本地文件，不允许自己重新拼标题、再补第二个 `# 标题`，也不允许把不相关视图混进同一文件
  - 如果用户只说“查看详情”并选择 `A`，导出完整详情 Markdown；如果用户明确说“导出 full / polish / original / summary / outline / highlights”，就只导出该视图
  - 默认导出目录：`~/Documents/AI好记导出/`
  - 文件名优先使用笔记标题；去掉 `/ \ : * ? " < > |` 等非法字符
  - 文件扩展名固定为 `.md`
  - 必须真正执行本地写文件，不允许只把 Markdown 文本回在聊天里就声称“已导出”
  - 如果导出目录不存在，要先创建目录
  - 写入完成后，必须回报最终保存的绝对路径
  - 导出 `.md` 时不分块，直接一次性生成完整 Markdown 文件
- `B`：直接在聊天里查看
  - 只有用户明确选择 `B` 后，才允许继续
  - 如果用户原请求是“看全文 / 看原文 / 看润色稿”，则直接进入对应长视图的聊天分块链路，不要先给详情概览
  - 如果用户原请求只是“看这篇笔记 / 查看详情 / 看详情 / 打开详情”，则先展示可选视图，再由用户指定继续看哪一种
  - `full`、`polish`、`original` 这类长内容必须使用对应 `semantic_view`，并从 `semantic_chunk_no=1` 开始
  - 每次回复只允许基于该次接口返回的 `semantic_markdown` 输出当前 chunk；如果用户要看下一段，再递增 `semantic_chunk_no`

推荐引导话术：

```text
这篇笔记你要怎么查看？

A：导出为 Markdown 文件到本地
B：直接在聊天里查看
```

强制规则：

- 当用户说“查看详情 / 看详情 / 打开详情 / 看这篇笔记 / 看全文 / 看原文 / 看润色稿”时，第一条回复只能是 `A / B` 选择问题
- 在用户没有明确回答 `A` 或 `B` 前，不允许输出详情概览、正文、引用摘录，或 `summary / outline / highlights / full / polish / original` 的任何内容
- 不允许把“我先给你详情概览”作为默认行为
- 只有用户明确选择 `B` 后，才能继续返回详情内容
- 只有用户明确选择 `A` 后，才能继续走本地 `.md` 导出
- `A` 路线必须优先使用接口返回的 `data.export_markdown`，不允许自己重新拼装重复标题或混合多个视图
- `full`、`original`、`polish` 在 `B` 路线下都视为长内容视图，必须与导出链路共享同一个 A/B 入口，不允许绕过询问直接开始发正文

### 场景 5：只看某个语义视图

用户说：

```text
看这篇笔记的大纲
看这篇笔记的精华速览
看这篇笔记的总结
看这篇笔记的润色稿
```

处理规则：

- 只返回用户当前指定的那一部分
- 不要把 `summary`、`outline`、`highlights`、`polish`、`original`、`full` 一次性全塞给用户
- `summary`、`outline`、`highlights` 默认一次性返回，不分页
- `polish`、`original`、`full` 必须带上对应的 `semantic_view`
- 第一次查看 `polish`、`original`、`full` 时，必须从 `semantic_chunk_no=1` 开始
- 回复里只能直接使用该次接口返回的 `semantic_markdown`
- 不允许把当前 chunk 改写成自己的总结、提炼、复述或补充说明
- 返回完当前 chunk 后，不要自动继续；要先询问用户是否继续看下一段
- 只有用户明确回答“继续 / 下一段 / 继续第 2 段 / 继续第 3 段”这类指令后，才把 `semantic_chunk_no` 递增再请求下一段
- 如果接口返回 `semantic_has_more=false`，要明确告诉用户当前已经是最后一段
- 如果用户选择导出 `.md`，则不走聊天分块，直接回到场景 4 的 `A` 路线，使用 `include_export_markdown=true`

对 `full`、`polish`、`original` 的额外硬约束：

- 聊天里只允许展示当前视图的当前 chunk，对应本次接口返回的 `data.semantic_markdown`
- 不允许在 `full` 的回复里混入 `summary`、`outline`、`highlights`
- 不允许在 `polish` 的回复里混入 `original`、`full` 或任何概括性说明
- 不允许在 `original` 的回复里混入 `polish`、`full` 或任何概括性说明
- 不允许在回复前后加“我的总结”“精华速览”“开头提炼”“模型概括”等额外内容
- 不允许把多个 chunk 拼在同一条正文回复里

当返回长内容分块时，推荐话术：

```text
这部分内容比较长。我先发你当前这一段；如果你要继续看下一段，直接回复“继续”就行。
```

推荐回复：

```text
我只发你当前请求视图的当前这一段内容；如果要下一段，直接回复“继续”。
```

### 场景 6：当前没有该语义内容

用户说：

```text
帮我看下这篇笔记的精华速览。
```

处理规则：

- 如果接口返回该视图为空、缺失、未生成，不能假装有内容
- 要明确告诉用户当前没有这部分
- 同时给出当前可替代的视图建议

推荐回复：

```text
这篇笔记当前还没有精华速览，你可以继续看总结、大纲或润色稿。
```

### 场景 7：查看笔记本树

用户说：

```text
列出我的笔记本
看一下笔记本
看 Ai好记 笔记本树
```

处理规则：

- 先调用 `GET /folders`
- 返回时用树状渐进格式
- 每个节点展示：
  - 笔记本名
  - 当前笔记本笔记数量
  - 创建时间
- 默认不展示 `folder_id`
- 如果存在层级关系，必须缩进展示
- 如果接口里有 `children`，必须用 `children` 的真实层级，不允许改写成扁平目录树
- 如果用户随后指定某个笔记本，再继续查该笔记本里的笔记

推荐回复：

```text
我先把当前 Ai好记 笔记本列表整理给你。你可以继续说“看Ai好记里的笔记”或“打开第 1 个笔记本”。
```

### 场景 8：查看某个笔记本里的笔记

用户说：

```text
看Ai好记笔记本里的笔记
看第 1 个笔记本里的笔记
```

处理规则：

- 如果用户说的是笔记本名称，必须先调用 `GET /folders`
- 在返回的笔记本树里定位对应节点，读取真实 `folder_id`
- 如果用户说的是列表里的自然顺序，例如“第 1 个笔记本”，按当前会话里最近一次展示的笔记本树映射到实际节点，再读取 `folder_id`
- 再调用 `GET /notes?page_no=<page_no>&page_size=<page_size>&folder_id=<folder_id>`
- 默认 `page_no=1`
- 默认 `page_size=10`
- 列表返回时继续使用自然编号，不展示 `note_id`
- 默认把“笔记本名称 / 创建时间 / 文件数 / 当前页笔记列表”一起展示
- 如果总数超过一页，明确告诉用户可以继续看下一页
- 只有用户明确说“搜和Ai好记相关的笔记 / 搜关键词Ai好记”，才允许走全量关键词搜索链路
- 只有用户明确说“看Ai好记笔记本里的关于Ai好记的笔记 / 找一下Ai好记笔记本里和Ai好记相关的笔记”这类话术时，才允许走“笔记本内关键词搜索”链路

强制约束：

- “看Ai好记笔记本里的笔记”固定走 `/folders -> folder_id -> /notes?folder_id=...`
- 在这条链路里，`Ai好记` 仅表示 `folder_name`
- 一旦已经用 `folder_name` 找到了 `folder_id`，后续 `/notes` 请求里必须视为 `keyword=None`
- 不允许退化成 `keyword=Ai好记`
- 不允许只返回 1 篇标题命中的候选就声称这是“该笔记本里的笔记”
- 不允许跳过 `/folders` 直接假设 `folder_id`
- 不允许把别的笔记本里的笔记混进当前笔记本列表

### 场景 8B：在某个笔记本里搜索相关笔记

用户说：

```text
找一下Ai好记笔记本里的关于Ai好记的笔记
找一下Ai好记笔记本里和Ai好记相关的笔记
搜一下Ai好记笔记本里提到Ai好记的笔记
```

处理规则：

- 必须先调用 `GET /folders`
- 先把第一个“Ai好记”识别为 `folder_name`
- 定位真实 `folder_id`
- 再把“关于Ai好记 / 和Ai好记相关 / 提到Ai好记”识别为 `keyword=Ai好记`
- 然后调用 `GET /notes?page_no=<page_no>&page_size=<page_size>&folder_id=<folder_id>&keyword=<keyword>`
- 返回时要明确说明这是“该笔记本内命中关键词的结果”，不是整本全部笔记
- 这类结果必须以 API 返回为准，不能再额外做“只保留标题里明确提到关键词”或“只保留讲这个团队本身”的二次语义收缩
- 如果按这条链路 API 返回 5 篇，就展示 5 篇；不要自行缩成 2 篇或别的数量

强制约束：

- 只有用户明确表达“在某个笔记本里搜索某关键词”时，才允许同时传 `folder_id + keyword`
- 如果用户只是说“看某个笔记本里的笔记”，绝不能偷偷补上 `keyword`
- `folder_name` 只负责定位笔记本，`keyword` 只负责做笔记本内筛选，两者不能因为文本相同就自动复用
- 不允许把 `keyword=Ai好记` 再解释成“严格相关”“标题明确提到”“讲Ai好记本身”等更窄的人工标准
- 不允许在拿到 API 搜索结果后再手动删减命中项

推荐回复：

```text
我先按笔记本链路把这个笔记本里的笔记列表整理给你；如果你要继续看下一页，直接说“下一页”。
```

### 5. 错误处理

- `401/403`：API Key 无效、已过期、已停用、已删除、无权限、当前 API Key 对应用户不是会员用户，或应用未正确绑定
- `404`：笔记不存在
- `429`：达到调用频率限制

如果是权限问题，要明确告诉用户：

- 应用需要有对应 scope
- Key 也需要有对应 scope

如果是 `401/403`，skill 不允许只返回“调用失败”这类模糊话术，必须直接告知用户当前 API Key 不可用，并提示可能原因，例如：

- API Key 已过期
- API Key 已被停用
- API Key 已被删除
- API Key 没有 `note:list` 或 `note:read` 权限
- 当前 API Key 对应用户不是会员用户
- API Key 对应应用或绑定关系失效

推荐回复：

```text
当前 Ai好记 API Key 已不可用，可能是已过期、已停用、已删除，或当前 Key 没有对应接口权限。
请到 AI好记开放平台检查这把 Key 的状态、权限范围和应用绑定关系后再重试。
```

如果接口明确返回当前用户不是会员用户，优先使用下面这句，不要改写成泛化报错：

```text
当前 API Key 对应用户不是会员用户，请先开通或续费会员后再调用 AI好记开放平台接口。
```

如果接口返回了明确错误信息，优先透传成用户能理解的表述，不要吞掉后端错误语义。

## 推荐决策表

| 用户意图 | 操作 |
|---|---|
| 查我的 Ai好记 | 调 `notes` 列表 |
| 列出我的笔记本 / 文件夹 / 笔记本树 | 先调 `folders`，按层级列表展示 |
| 看某个笔记本 / 文件夹里的笔记 | 先定位笔记本，再调 `notes?...&folder_id=...` |
| 查最近 N 篇 / 最新 N 篇 | 调 `notes?page_no=1&page_size=N&sort_mode=create_time&sort_order=desc`，未给数量时默认 `N=10` |
| 查最老 N 篇 / 最早 N 篇 | 调 `notes?page_no=1&page_size=N&sort_mode=create_time&sort_order=asc`，未给数量时默认 `N=10` |
| 找和某个主题相关的 AI好记内容 | 调 `notes?keyword=...` |
| 按某个 URL 找 AI好记内容 | 调 `notes?keyword=<url>`，优先按返回的 `url` 精确匹配 |
| 看某条 AI好记详情 | 先定位 `note_id`，再调详情 |
| 看这条 AI好记的总结 | `semantic_view=summary` |
| 看这条 AI好记的精华速览 | `semantic_view=highlights` |
| 看这条 AI好记的大纲 | `semantic_view=outline` |
| 看这条 AI好记的润色 | `semantic_view=polish`，长内容按 `semantic_chunk_no` / `semantic_chunk_size` 分块 |
| 看这条 AI好记的原文 | `semantic_view=original`，长内容按 `semantic_chunk_no` / `semantic_chunk_size` 分块 |
| 看全部 | `semantic_view=full`，长内容按 `semantic_chunk_no` / `semantic_chunk_size` 分块 |

## 参考文档

- `references/agent-open-platform.md`
