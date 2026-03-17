---
title: "OMAR 正式发布"
description: "基于 Rust 和 tmux 构建的智能体编排 TUI"
date: "2026-03-07"
author: "OMAR 团队"
---

我们推出 **OMAR**（one-man army）—— 一个用于创建强大智能体组织的 TUI 工具。

## 为什么做 OMAR？

AI 编程智能体单独使用时已经很强大了，但真实项目需要团队。你需要智能体能并行工作、各有专长，并且协调配合 —— 就像一家公司。

OMAR 给你一个终端仪表盘，让你在一个地方编排所有这一切。

## 你能做什么？

- **深层层级** —— 构建任意深度的并行组织结构
- **异构后端** —— 让 Claude、Codex、Cursor 和 Opencode 协同工作
- **完全掌控** —— 导航到任意层级的任意智能体，直接交互
- **集成** —— 将智能体连接到 Slack 频道，或赋予桌面操控能力
- **事件驱动协调** —— 在智能体之间安排状态检查、交接和提醒

## 工作原理

OMAR 运行在 tmux 之上。每个智能体拥有独立的 tmux 会话，OMAR 的 TUI 仪表盘统一监控。你从执行助理（EA）开始，给它一个高层任务，然后观察它并行创建工作智能体。

```bash
$ curl -fsSL https://omarmy.ai/install.sh | sh
$ omar
```

用方向键导航，深入智能体层级，通过弹窗附加到任何智能体。全键盘驱动，快速高效。

## 技术栈

- **Rust** —— 快速、安全、单一二进制
- **ratatui** —— TUI 框架
- **tmux** —— 久经考验的会话管理
- **HTTP API** —— 后端无关的编排接口，端口 9876

## 支持的后端

| 后端                                                                                    | 启动方式                        |
| --------------------------------------------------------------------------------------- | ------------------------------- |
| [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) | `omar` 或 `omar --agent claude` |
| [Codex CLI](https://developers.openai.com/codex/cli)                                    | `omar --agent codex`            |
| [Opencode](https://github.com/anomalyco/opencode)                                       | `omar --agent opencode`         |
| [Cursor CLI](https://cursor.com/cli)                                                    | `omar --agent cursor`           |

查看[文档](/zh/docs/)开始使用，加入我们的 [Discord](https://discord.gg/X76PSzmfWr) 与社区交流。
