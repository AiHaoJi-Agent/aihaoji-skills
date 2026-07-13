# Ai好记开放平台 Skill 开发指引

## Setup & Commands

- 安装或绑定：`npm run setup`（交互式）或 `npx aihaoji-openclaw setup`；会校验 API Key 并写入用户配置。
- 文档校验：`npm run check:docs`；单元测试：`npm test`。
- `npm run check` 会读取已配置的 OpenClaw API Key 并请求线上 notes 接口，仅在具备有效授权时执行。

## Code Style

- `SKILL.md` 与 `references/agent-open-platform.md` 是接口和交互规范的事实源；修改能力时同步更新相应说明与校验。
- Node 脚本使用 ESM，Python 脚本沿用 4 空格缩进、标准库优先和清晰的错误输出。
- 接口路径、字段名和用户可见文案必须与开放平台契约一致。

## Testing

- 修改 Skill 或参考文档后运行 `npm run check:docs` 和 `npm test`。
- 改动安装、鉴权或接口探测时，在已授权的测试账号执行 `npm run check`；不得以真实密钥写入测试输出。

## PR Rules

- 从最新 `origin/main` 新建 `feature_xxx`；提交信息使用中文。
- PR 写明接口/字段、Skill 行为和配置写入范围，并附文档校验、单测及授权接口验证结果。
- 影响写入行为或用户确认步骤的改动必须单独说明兼容性与回读验证。

## Do-not Rules

- 不提交、打印或硬编码 API Key、用户配置、笔记内容、内部 ID 或接口响应中的敏感数据。
- 不扫描本地目录、缓存、日志或源码来猜测用户笔记；查询必须调用开放平台接口。
- 不编造 `folder_id`、`target_folder_id`、`note_id` 或 `move_item_list[].item_id`，全部必须来自接口返回。
- 未展示变更计划并得到用户明确确认，不得创建、重命名、删除或移动笔记本/笔记；删除必须单独确认。
