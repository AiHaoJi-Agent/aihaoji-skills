# Ai好记 Skills 开发指引

## 项目边界

- 可分发 Skill 位于 `skills/aihaoji/`。
- Skill 行为规范以 `skills/aihaoji/SKILL.md` 为准。
- API 字段、接口示例和场景契约以 `skills/aihaoji/references/agent-open-platform.md` 为准。
- 修改能力时，同时检查 Server 实现、前端开放平台文档和本仓库 Skill 文档，避免三端契约漂移。

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
python3 /Users/aihaoji/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/aihaoji
npm pack --dry-run --json
git diff --check
```

`npm run check` 会真实请求开放平台，只能在已明确配置测试授权时运行；不得把 Key、笔记内容或接口响应原文写入日志、测试输出或提交。

## 安全与范围

- 不提交 `.env`、用户配置、API Key、真实笔记内容、临时构建包或 `.plugin-eval/`。
- 不通过扫描本地目录、缓存、日志或源码猜测用户笔记；运行时查询必须走开放平台接口。
- 不编造接口返回的 ID 或权限信息；写入、移动和删除行为必须遵循 `SKILL.md` 中的确认与回读规则。
- 保持修改窄而可验证，避免顺手重构与本次功能无关的文件。
