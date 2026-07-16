# Ai好记 Skills 开发指引

## 项目边界

- 可分发 Skill 位于 `skills/aihaoji/`。
- Skill 行为规范以 `skills/aihaoji/SKILL.md` 为准。
- API 字段、接口示例和场景契约以 `skills/aihaoji/references/agent-open-platform.md` 为准。
- 修改开放平台能力时，应对照公开 API 契约；有相关仓库访问权限时，同时检查 Server 实现和前端开放平台文档，避免契约漂移。

## 常用命令

- 安装器开发入口：`npm run setup`；本地 Python 安装器：`npm run install:local`。
- 在线接口探测：`npm run check`，只在明确配置测试授权时运行。
- Node 脚本使用 ESM；Python 脚本使用 4 空格缩进、标准库优先，并输出清晰、可定位的错误信息。
- 接口路径、字段名、权限名和用户可见文案必须与开放平台契约一致。

## 分支与发布

团队采用以下并行开发流程：

```text
main -> feature/<topic> -> PR to dev -> test
                                 |
                     tested feature PR to main
```

- 每个功能分支从最新 `main` 创建，分支名使用 `feature/<topic>`。
- 功能分支先向 `dev` 创建 PR，完成对应测试后，再以同一功能分支向 `main` 创建 PR。
- `main` PR 只能包含当前功能的提交，不得把 `dev` 中其他未完成功能带入。
- 创建 PR 前先同步目标分支，检查 `git diff <target>...HEAD` 和工作区状态。
- 提交信息使用中文；PR 说明变更范围、兼容性影响和验证结果。

## 本地验证

修改代码、Skill 文档、安装器或测试后，运行：

```bash
npm test
python3 scripts/check_skill_docs.py
python3 -m compileall -q skills/aihaoji/scripts scripts/check_skill_docs.py tests/test_scripts.py
npm run validate:skill
npm pack --dry-run --json
git diff --check
```

`npm run check` 会真实请求开放平台，只能在已明确配置测试授权时运行；不得把 Key、笔记内容或接口响应原文写入日志、测试输出或提交。

测试分层：文档和纯逻辑修改至少运行单元测试、文档检查和官方 Skill 校验；安装器、鉴权或接口探测修改还要运行对应 Node/Python 测试，并在安全的测试授权环境中运行 `npm run check`。

## Agent 平台兼容性

- 当前支持平台以 README 和 `SKILL.md` 的兼容性说明为准，包括 Codex、OpenClaw、Claude Code 和 Hermes Agent。
- 修改 `SKILL.md`、`agents/`、安装器、Skill 目录布局或发布配置后，应关注各支持平台最新稳定版本的兼容性。
- 统一按 `docs/agent-platform-compatibility.md` 中的标准用例执行触发、误触发和真实工作流验证。
- 最低验证范围包括 Skill 安装、Skill 发现、指令触发、共享配置读取，以及至少一个只读能力的冒烟测试。
- 发布前在 PR 中记录平台版本、操作系统、安装方式、验证结果和验证日期；未实际验证的平台应明确标记为“未验证”。
- 不在本文件固定具体平台版本号，避免版本信息过期；具体版本以对应发布 PR 的兼容性记录为准。
- 真实接口测试只能使用安全的测试授权，不得记录 API Key、真实笔记内容或接口响应原文。

## PR 要求

- PR 说明接口或字段变更、Skill 行为、配置写入范围和兼容性影响。
- 涉及写入、移动、删除或用户确认步骤时，说明确认流程、回读验证和失败处理。
- 不把未完成的其他功能、临时评估结果或无关重构带入当前功能 PR。

## 安全与范围

- 不提交 `.env`、用户配置、API Key、真实笔记内容、临时构建包或 `.plugin-eval/`。
- 不通过扫描本地目录、缓存、日志或源码猜测用户笔记；运行时查询必须走开放平台接口。
- 不编造接口返回的 ID 或权限信息；写入、移动和删除行为必须遵循 `SKILL.md` 中的确认与回读规则。
- 保持修改窄而可验证，避免顺手重构与本次功能无关的文件。
