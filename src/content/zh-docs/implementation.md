---
title: "实现细节"
description: "OMAR 的技术栈、项目结构和关键模块"
order: 3
---

## 技术栈

| 组件     | 选型                     | 理由                         |
| -------- | ------------------------ | ---------------------------- |
| 语言     | Rust                     | 内存安全、高并发、单一二进制 |
| TUI      | ratatui 0.29 + crossterm | 社区活跃、性能优秀           |
| 异步     | tokio（完整版）          | 行业标准                     |
| HTTP     | axum 0.7                 | 符合人体工学、基于 tower     |
| CLI      | clap 4（derive 模式）    | 用户体验优秀                 |
| 配置     | toml + serde             | Rust 原生支持                |
| 错误处理 | anyhow + thiserror       | 简洁高效                     |

## 项目结构

```
omar/
├── Cargo.toml              # 工作区根配置
├── src/
│   ├── main.rs             # 入口、CLI 解析、tmux 重启
│   ├── app.rs              # 核心状态机、刷新/渲染
│   ├── config.rs           # 配置加载 + 自动检测
│   ├── event.rs            # 输入/定时事件处理
│   ├── memory.rs           # 持久化状态管理
│   ├── computer.rs         # X11 桌面操控集成
│   ├── projects.rs         # 项目增删改查
│   ├── api/
│   │   ├── mod.rs          # 路由设置
│   │   ├── handlers.rs     # HTTP API 端点（axum）
│   │   └── models.rs       # 请求/响应类型
│   ├── tmux/
│   │   ├── mod.rs          # 模块根
│   │   ├── client.rs       # tmux 命令封装
│   │   ├── session.rs      # 会话类型
│   │   └── health.rs       # 健康检查
│   ├── manager/
│   │   └── mod.rs          # 执行助理会话生命周期
│   ├── scheduler/
│   │   ├── mod.rs          # 事件调度 + 投递
│   │   └── event.rs        # ScheduledEvent 类型 + 排序
│   └── ui/
│       ├── mod.rs          # 模块根
│       └── dashboard.rs    # TUI 渲染
├── bridges/
│   ├── omar-slack-bridge/  # Slack 桥接 crate
│   └── omar-computer-bridge/ # 桌面操控桥接 crate
└── prompts/                # 内嵌的提示词模板
```

## 关键模块

### main.rs（约 833 行）

入口点，使用 clap 解析 CLI。如果当前不在 tmux 会话中，会自动在 tmux 内重新启动。管理守护进程生命周期、桥接自动启动，以及优雅关闭（先 SIGTERM 后 SIGKILL）。

### app.rs（约 1,460 行）

核心应用状态机。管理智能体列表、选择、焦点、项目和 UI 状态。处理刷新周期，轮询 tmux 获取会话更新。构建层级命令树以可视化智能体。

### api/handlers.rs（约 1,039 行）

基于 axum 的完整 REST API，启用了 CORS。包含智能体增删改查（支持 `backend` 和 `model` 字段实现异构创建）、事件调度、桌面操控和项目管理端点。支持会话名称规范化（短名称如 "auth" 会解析为 "omar-agent-auth"）。

### scheduler/mod.rs

使用 BinaryHeap（按时间戳排序的最小堆）实现事件调度系统。支持一次性和周期性事件。通过 `send-keys` 向智能体 tmux 会话注入文本来投递事件。使用 `Arc<Mutex<>>` 保证线程安全。

### memory.rs

持久化状态快照。将活跃状态（项目、智能体、任务）写入 `~/.omar/memory.md`。启动时注入到执行助理提示词中，实现上下文延续。

## CLI 接口

```bash
# 启动仪表盘（默认 - 自动检测后端）
omar

# 指定智能体后端
omar --agent opencode

# 自定义配置
omar --config ~/.config/omar/config.toml

# 创建新智能体
omar spawn --name my-agent --command "claude"

# 列出智能体（非 TUI 模式）
omar list

# 终止智能体
omar kill agent-1

# 启动执行助理
omar manager start

# 配置 tmux
omar setup-tmux
```

## 自动检测

启动时，OMAR 会自动检测可用的智能体后端：

1. 检查 PATH 中是否有 `claude` → `claude --dangerously-skip-permissions`
2. 回退到 `codex` → `codex --no-alt-screen --dangerously-bypass-approvals-and-sandbox`
3. 回退到 `cursor` → `cursor agent --yolo`
4. 回退到 `opencode`
5. 可通过 `--agent <name>` 手动覆盖（支持：claude、codex、cursor、opencode）

## 桥接

两个桥接都是可选的，在环境满足条件时自动启动：

- **Slack 桥接**：当设置了 `SLACK_BOT_TOKEN` 和 `SLACK_APP_TOKEN` 时自动启动。通过 API 将 Slack 消息路由到 OMAR 智能体。
- **桌面操控桥接**：当设置了 `DISPLAY` 时自动启动。提供 X11 鼠标/键盘/截屏控制，每次只允许一个智能体独占使用。

## 内嵌提示词

`/prompts/` 目录下的提示词会编译进二进制文件，首次运行时同步到 `~/.omar/prompts/`：

- `executive-assistant.md` —— 执行助理系统提示词（前置记忆上下文）
- `agent.md` —— 统一智能体提示词（为所有创建的智能体注入）
- `prompts/tests/` —— 测试场景，如 `project-factory.md`
