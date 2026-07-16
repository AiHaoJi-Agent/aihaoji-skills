# Ai好记 Skill

[![License: MIT-0](https://img.shields.io/badge/License-MIT--0-blue.svg)](https://opensource.org/licenses/MIT-0)
[![skills.sh](https://skills.sh/b/AiHaoJi-Agent/aihaoji-skills)](https://skills.sh/AiHaoJi-Agent/aihaoji-skills)

Ai好记 Skill 让 Codex、OpenClaw、Claude Code、Hermes Agent 等兼容 Agent Skills 的平台连接你的 Ai好记知识库，在聊天中查找、阅读、导出和整理笔记，并管理笔记本。

## 适用场景

- `帮我看最近的笔记`
- `帮我找Ai好记相关的内容`
- `帮我找这个 URL 对应的笔记：https://www.bilibili.com/video/BV...`
- `帮我看这篇笔记的总结、原文或大纲`
- `帮我读取这篇笔记的划线和批注`
- `新建一个笔记本叫产品研究`
- `把这几篇笔记移动到产品研究`
- `帮我把 2026年7月2日 的笔记自动归类整理`

## 核心能力

| 能力 | 说明 |
|---|---|
| 查找笔记 | 查看最近笔记，或按关键词、标题、时间、笔记本和原始 URL 查找已有笔记 |
| 按链接找笔记 | 使用原始内容 URL 定位对应的 Ai好记笔记 |
| 阅读详情 | 查看总结、大纲、精华速览、润色稿、原文和完整内容 |
| 导出 Markdown | 使用详情接口返回的 Markdown 内容导出单篇笔记 |
| 读取用户记录 | 查看划线、高亮、批注和我的记录，作为阅读和整理依据 |
| 管理笔记本 | 新建、重命名、删除和移动笔记本，写入前先展示操作计划 |
| 移动整理笔记 | 把单篇或多篇笔记移动到指定笔记本，并回读验证结果 |
| 自动归类整理 | 读取笔记和用户记录，生成归类计划，经确认后创建笔记本并移动笔记 |

## 安装

安装 Skill，让不同 Agent 平台都可以使用：

```bash
npx skills add AiHaoJi-Agent/aihaoji-skills -g
```

`-g` 表示为当前用户安装。此命令会安装到检测到的兼容 Agent，无需逐个平台重复安装。

## 配置 API Key

首次使用时，直接告诉 Agent 你想查找或整理哪些笔记。若尚未配置 API Key，Agent 会引导你完成：

1. 前往 [Ai好记开放平台](https://openapi.aihaoji.com) 创建开发者密钥。
2. 按照当前 Agent 的提示完成授权。
3. 当前 Agent 会在你授权后完成校验并保存到当前电脑，然后继续处理刚才的请求。

同一台电脑上的 Codex、OpenClaw、Claude Code 和 Hermes Agent 可以共用一次配置，无需在不同 Agent 中重复配置。请妥善保管 API Key，不要公开分享。

## 许可证

[MIT-0](LICENSE)
