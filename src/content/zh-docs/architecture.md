---
title: "架构与设计"
description: "OMAR 的架构 —— TUI 仪表盘如何通过 tmux 和 MCP 管理智能体"
order: 2
---

## 概览

OMAR 是一个基于 tmux 的 TUI 仪表盘，用于编排 AI 编程智能体。智能体通过类型化的 **MCP（Model Context Protocol）工具接口** 驱动整个系统，每个智能体拥有自己的 `omar mcp-server` stdio 子进程。系统不监听任何端口 —— 每个智能体都通过自己私有的 stdin/stdout 上的 JSON-RPC 与 OMAR 通信。

## 架构图

```
tmux server
├── omar-dashboard            （TUI 会话，驱动用户界面）
│
├── omar-agent-ea-0           （EA 0 的执行助理）
├── omar-agent-ea-1           （EA 1 的执行助理，可选）
├── omar-agent-0-worker1      （claude，归属于 EA 0）
├── omar-agent-0-worker2      （codex， 归属于 EA 0）
└── omar-agent-1-research     （gemini，归属于 EA 1）
                │
                ▼  每个智能体派生自己的 MCP 子进程
        ┌─────────────────────────────────────────┐
        │  omar mcp-server (stdio JSON-RPC)       │
        │  绑定到该智能体的启动 EA                │
        │  约 30 个类型化工具：                   │
        │    spawn_agent, kill_agent, send_input, │
        │    list_agents, get_agent,              │
        │    add_project, complete_project,       │
        │    schedule_omar_event, list_events,    │
        │    list_eas, switch_ea, create_ea,      │
        │    log_justification, slack_reply,      │
        │    computer_*, ...                      │
        └─────────────────────────────────────────┘

磁盘上的状态：    ~/.omar/ea/<id>/{worker_tasks,task_registry,...}.json
                  ~/.omar/{config.toml, eas.json, active_ea, ...}
```

仪表盘、智能体、Slack 桥接，以及任何外部客户端，都汇聚到 `~/.omar/` 下的同一份磁盘状态上。它们之间从不直接通信。

## 核心组件

### 工作区结构

OMAR 是一个 Rust 工作区，包含 3 个二进制 crate：

- **`omar`** —— 主程序：TUI 仪表盘、MCP stdio 服务器（`omar mcp-server`）、事件调度器、manager 子命令
- **`omar-slack-bridge`** —— Slack Socket Mode 集成；自己派生 `omar mcp-server` 子进程
- **`omar-computer-bridge`** —— X11 桌面操控辅助进程（鼠标、键盘、截屏）

### 多 EA（Multi-EA）

OMAR 支持并行运行多个执行助理。每个 EA 拥有：

- 一个 tmux 管理会话（`omar-agent-ea-<id>`）
- 一个工作智能体命名空间（`omar-agent-<id>-<name>`）
- 一个状态目录（`~/.omar/ea/<id>/`）
- 隔离的项目板、记忆、事件队列

EA 注册表 `eas.json`、`active_ea` 指针，以及每个 EA 的状态目录都由 `src/ea.rs` 管理。智能体绑定在它的启动 EA 上 —— `switch_ea` 只会切换仪表盘的默认值；已经在运行的 MCP 子进程仍然停留在原本的 EA 上。

### 会话类型

- **仪表盘**：`omar-dashboard` —— TUI 会话（启动时自动创建）
- **管理器 / EA**：`omar-agent-ea-<id>` —— EA 的 tmux 会话，每个 EA 一个
- **工作智能体**：`omar-agent-<ea_id>-<name>` —— 由 EA 通过 `spawn_agent` 创建

### 统一智能体模型

除执行助理外，所有智能体都接收 `agent.md` 作为系统提示词。每个被派生的智能体都是自治的：它接到任务，决定亲自完成还是通过 `spawn_agent` 派生子智能体，最后报告完成。执行助理接收 `executive-assistant.md`，并在其前面拼接记忆上下文。

### 父子层级

智能体的父子关系记录在 `~/.omar/ea/<id>/agent_parents.json` 中。TUI 将其渲染为可导航的命令树。任何智能体都可以派生子智能体，从而形成任意深度的层级。

## 智能体如何连接到 MCP 服务器

管理器在派生每个智能体之前，会写入按 EA 划分的启动上下文（`~/.omar/mcp/ea-<id>/context.json`），并配置后端的 MCP 集成方式以启动 `omar mcp-server --context-file <path>`：

| 后端     | 集成方式                                                            |
| -------- | ------------------------------------------------------------------- |
| Claude   | `~/.omar/mcp/ea-<id>/claude-mcp.json`，通过 `--mcp-config` 引用     |
| Codex    | `-c mcp_servers.omar.command=…` / `mcp_servers.omar.args=…`         |
| Cursor   | 写入 `~/.cursor/mcp.json` 中的条目（键为 `omar-ea-<id>`）            |
| Gemini   | `gemini mcp add -s user omar <omar> mcp-server --context-file …`    |
| Opencode | 通过环境变量指向 `omar mcp-server --context-file …`                 |

每个后端自己启动 `omar mcp-server` 子进程；启动时被烤进上下文的 EA id 让每个智能体天然带上 EA 绑定，无需为每次工具调用传递路由参数。

## 健康监控

健康状态通过比较两次刷新帧之间窗格内容是否变化来判断：

| 状态    | 图标 | 含义                              |
| ------- | ---- | --------------------------------- |
| Running | ●    | 自上次检查以来窗格内容发生了变化  |
| Idle    | ○    | 未检测到输出变化                  |

## 仪表盘界面布局

1. **状态栏**（顶部） —— 智能体计数、事件倒计时、警告
2. **智能体网格** —— 每个智能体一张卡片，按健康状态排序
3. **聚焦面板** —— 选中智能体的输出 + 命令树
4. **帮助栏**（底部） —— 快捷键说明

## 持久化状态

```
~/.omar/
├── config.toml                       # 用户配置
├── eas.json                          # EA 注册表
├── active_ea                         # 仪表盘 / CLI 默认 EA 指针
├── ea_next_id                        # 单调递增的 EA id 高水位标记
├── ea/<id>/
│   ├── worker_tasks.json             # 智能体 → 任务映射
│   ├── task_registry.json            # 权威任务记录
│   ├── agent_parents.json            # 父子关系
│   ├── memory.md                     # EA 记忆快照
│   ├── ea_prompt_combined.md         # 渲染后的 EA 系统提示词
│   └── status/<session>.md           # 智能体自报状态
├── mcp/ea-<id>/
│   ├── context.json                  # 给派生智能体使用的 McpLaunchContext
│   ├── claude-mcp.json               # Claude --mcp-config 的目标
│   └── gemini-deny-native-wake.toml  # 各后端唤醒工具的禁用清单
├── slack_outbox/                     # 待投递的 slack_reply MCP 输出
├── scheduled_events.json             # 持久化事件队列（重启后恢复）
├── prompts/                          # 同步的提示词模板
├── logs/panics/                      # 持久化的 panic 转储
└── manager_notes_ea<id>.md           # 每个 EA 用 shell heredoc 写下的笔记
```

## 配置

```toml
# ~/.omar/config.toml

[dashboard]
refresh_interval = 1
session_prefix = "omar-agent-"
show_event_queue = true
sidebar_right = true
show_quotes = false

[health]
idle_warning = 15
idle_critical = 300
error_patterns = ["error", "failed", "rate limit", "exception"]

[agent]
default_command = "claude --dangerously-skip-permissions"
default_workdir = "."

[watchdog]
command = ""                          # 空字符串 = 关闭看门狗
slack_channel = ""

[metrics]
spawn_metrics_enabled = false         # 可选的 ~/.omar/metrics/spawn_metrics.jsonl

[slack_bridge]
# active_ea = "Research"              # 通过仪表盘的设置面板（按 'S'）
                                      # 或手动编辑设置；Slack 桥接会
                                      # 在下一条入站消息时读到变更，
                                      # 无需重启进程。
```

后端会从已安装的工具中自动检测（Claude Code、Codex、Cursor、Gemini、Opencode），也可用 `--agent` 覆盖。Slack 桥接的目标 EA 取自 `[slack_bridge].active_ea`；若缺失或解析失败，桥接会在运行时回退到第一个已注册的 EA。

## 快捷键

| 按键                 | 动作                              |
| -------------------- | --------------------------------- |
| `←/→` 或 `h/l`       | 切换面板（侧栏 / 主区）           |
| `↑/↓` 或 `j/k`       | 上下移动选中项                    |
| `Tab`                | 钻入选中的智能体                  |
| `Shift+Tab` 或 `Esc` | 返回（向上钻出）                  |
| `Enter`              | 接入选中的智能体                  |
| `n`                  | 派生新的智能体                    |
| `d`                  | 杀死选中的智能体                  |
| `N`                  | 派生新的 EA（弹出输入名称）       |
| `D`                  | 删除当前 EA                       |
| `[`                  | 上一个 EA                         |
| `]`                  | 下一个 EA                         |
| `p`                  | 添加项目                          |
| `e`                  | 显示已调度的事件                  |
| `S`                  | 设置（含 Slack 桥接的 EA）        |
| `G`                  | 调试控制台                        |
| `r`                  | 刷新智能体列表                    |
| `z`                  | 分离（仪表盘继续在后台运行）      |
| `?`                  | 切换帮助                          |
| `Q`                  | 退出                              |
