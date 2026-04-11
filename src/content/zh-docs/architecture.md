---
title: "架构与设计"
description: "OMAR 的架构 —— TUI 仪表盘如何通过 tmux 管理智能体"
order: 2
---

## 概览

OMAR 是一个基于 tmux 的 TUI 仪表盘，用于编排 AI 编程智能体。它提供实时终端界面、HTTP API，以及 Slack 和桌面操控的集成桥接。

## 架构图

```
┌─ tmux 服务器 ──────────────────────────────────────────────┐
│                                                             │
│  ┌─ omar-dashboard（会话）──────────────────────────────┐  │
│  │                                                       │  │
│  │  ┌─ TUI 仪表盘 ──────────────────────────────────┐  │  │
│  │  │ 智能体：3 运行中 / 2 空闲                      │  │  │
│  │  │ ┌─────────┐ ┌─────────┐ ┌─────────┐            │  │  │
│  │  │ │ agent-1 │ │ agent-2 │ │ agent-3 │            │  │  │
│  │  │ │ ● 运行  │ │ ○ 空闲  │ │ ● 运行  │            │  │  │
│  │  │ └─────────┘ └─────────┘ └─────────┘            │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  │                                                       │  │
│  │     ┌─ tmux 弹窗 ─────────────────────┐            │  │
│  │     │ $ claude                          │            │  │
│  │     │ > 正在分析 src/auth.py...        │            │  │
│  │     └───────────────────────────────────┘            │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ omar-agent-ea ─────┐  ┌─ omar-agent-worker1 ────┐      │
│  │ 执行助理            │  │ claude 工作中...        │      │
│  └─────────────────────┘  └─────────────────────────┘      │
│                                                             │
│  ┌─ HTTP API (:9876) ─────────────────────────────────────┐ │
│  │ REST 端点：智能体创建、消息传递、事件调度               │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 工作区结构

OMAR 是一个 Rust 工作区，包含 3 个 crate：

- **`omar`** —— 主程序：TUI 仪表盘、HTTP API、事件调度器
- **`omar-slack-bridge`** —— Slack Socket Mode 集成
- **`omar-computer-bridge`** —— X11 桌面操控（鼠标、键盘、截屏）

### 会话类型

- **仪表盘**：`omar-dashboard` —— TUI 会话（启动时自动创建）
- **执行助理**：`omar-agent-ea` —— 自动启动的管理智能体
- **工作智能体**：`omar-agent-<name>` —— 由执行助理或 API 创建

### 统一智能体模型

所有智能体使用相同的角色 —— 代码中没有 PM/Worker 的区分。除执行助理外，每个智能体都接收 `agent.md` 作为系统提示词。执行助理接收 `executive-assistant.md`，并附带记忆上下文。

### 父子层级

智能体通过 `~/.omar/agent_parents.json` 跟踪父子关系。TUI 将其渲染为可导航的命令树，使用 Unicode 制表符绘制。用方向键即可深入子智能体。

## 健康监控

健康状态通过刷新帧之间面板内容的变化来判断：

| 状态   | 图标 | 含义                       |
| ------ | ---- | -------------------------- |
| 运行中 | ●    | 自上次检查后面板内容有变化 |
| 空闲   | ○    | 未检测到输出变化           |

## 仪表盘 UI 布局

1. **状态栏**（顶部）—— 智能体计数、事件倒计时、警告
2. **智能体网格**（55%）—— 每个智能体的卡片，按健康状态排序
3. **聚焦面板**（33%）—— 选中智能体的输出 + 命令树
4. **帮助栏**（底部）—— 快捷键提示

## 持久化状态

```
~/.omar/
├── memory.md                  # 活跃状态快照
├── tasks.md                   # 项目列表
├── worker_tasks.json          # 智能体任务分配
├── agent_parents.json         # 父子关系
├── status/<session>.md        # 智能体自报告状态
└── prompts/                   # 同步的提示词模板
```

## 配置

```toml
# ~/.omar/config.toml

[dashboard]
refresh_interval = 1
session_prefix = "omar-agent-"

[health]
idle_warning = 15
idle_critical = 300
error_patterns = ["error", "failed", "rate limit", "exception"]

[agent]
default_command = "claude --dangerously-skip-permissions"
default_workdir = "."

[api]
enabled = true
host = "127.0.0.1"
port = 9876

[watchdog]
command = ""  # 空 = 禁用；见下方"看门狗"
slack_channel = ""  # 告警 Slack 频道 ID
```

智能体后端会自动检测已安装的工具（Claude Code、Codex、Cursor 或 Opencode），也可通过 `--agent` 参数手动指定。

### 看门狗

当后端认证过期（如 Claude 订阅登录失效），OMAR 可自动检测故障并使用免费后端生成一个看门狗智能体，监控错误状态并通过 Slack 通知用户。原智能体保持运行，后端恢复后可继续工作。

**前提条件**：已安装 [opencode](https://opencode.ai)，已通过 `opencode /connect` 连接 [OpenRouter](https://openrouter.ai) 账户。

```toml
[watchdog]
# 通过 opencode 使用 OpenRouter 免费模型路由
command = "opencode --model openrouter/openrouter/free"

# 告警 Slack 频道 ID（可选）
slack_channel = "C0123456789"

# 触发看门狗的匹配模式（不区分大小写，以下为默认值）
auth_failure_patterns = [
  "please run /login",
  "401 unauthorized",
]
```

触发时，OMAR 会：
1. 检测智能体面板输出中的认证失败模式
2. 生成一个看门狗智能体监控所有会话
3. 看门狗通过 Slack 发送告警并定期检查智能体健康状态
4. 在仪表盘显示持久警告横幅

不会向看门狗智能体传递任何 API 密钥或机密信息。

## 快捷键

| 按键           | 操作                      |
| -------------- | ------------------------- |
| `↑/↓` 或 `j/k` | 切换智能体                |
| `→` 或 `Tab`   | 深入子智能体              |
| `←`            | 返回上级                  |
| `Enter`        | 附加到智能体（tmux 弹窗） |
| `n`            | 创建新智能体              |
| `d`            | 删除智能体（需确认）      |
| `p`            | 添加项目                  |
| `e`            | 显示事件                  |
| `r`            | 刷新                      |
| `z`            | 脱离 tmux                 |
| `D`            | 调试控制台                |
| `?`            | 帮助                      |
| `Q`            | 退出（需确认）            |
