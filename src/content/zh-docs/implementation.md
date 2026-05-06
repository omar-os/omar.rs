---
title: "实现细节"
description: "OMAR 的技术栈、项目结构和关键模块"
order: 3
---

## 技术栈

| 组件        | 选择                       | 理由                                       |
| ----------- | -------------------------- | ------------------------------------------ |
| 语言        | Rust                       | 内存安全、并发、单一可执行文件             |
| TUI         | ratatui 0.29 + crossterm   | 社区活跃，性能好                           |
| 异步        | tokio (full)               | 行业标准                                   |
| MCP 服务器  | 手写的 stdio JSON-RPC      | 同时支持按行分隔与 Content-Length，无额外依赖 |
| CLI         | clap 4 (derive)            | 体验出色                                   |
| 配置        | toml + toml_edit + serde   | 用 toml_edit 做局部写入时保留其他段        |
| 错误处理    | anyhow + thiserror         | 顺手好用                                   |
| 持久化      | 临时文件 + rename 原子写入 | 写入中途崩溃也不破坏数据                   |

## 项目结构

```
omar/
├── Cargo.toml              # 工作区根（workspace + omar 二进制）
├── src/
│   ├── main.rs             # 入口、CLI、tmux 重新启动逻辑
│   ├── app.rs              # 核心状态机，刷新与渲染
│   ├── config.rs           # 配置加载与自动检测
│   ├── ea.rs               # EA 注册表、id 分配、选择器解析
│   ├── event.rs            # 输入与 tick 事件处理
│   ├── memory.rs           # 持久化状态管理
│   ├── computer.rs         # X11 桌面操控集成
│   ├── projects.rs         # 项目 CRUD
│   ├── metrics.rs          # 可选的派生指标 JSONL 落盘
│   ├── backend_probe.rs    # list_backends 用的有界 `--version` 探测
│   ├── process.rs          # PID 存活检测 + 过期锁识别
│   ├── panic_hook.rs       # 把 panic 写到 ~/.omar/logs/panics
│   ├── mcp.rs              # MCP stdio 服务器（JSON-RPC，~30 个类型化工具）
│   ├── tmux/
│   │   ├── mod.rs
│   │   ├── client.rs       # tmux 命令封装、deliver_prompt、popup
│   │   └── health.rs       # 健康检查、鉴权失败检测
│   ├── manager/
│   │   └── mod.rs          # EA 会话生命周期、MCP 上下文落盘
│   ├── scheduler/
│   │   ├── mod.rs          # 持久化事件调度与投递
│   │   └── event.rs        # ScheduledEvent 类型与排序
│   └── ui/
│       ├── mod.rs
│       └── dashboard.rs    # TUI 渲染、设置面板
├── bridges/
│   ├── slack/              # Slack 桥接（omar-slack）
│   └── computer/           # 桌面操控桥接（omar-computer）
├── prompts/                # 内嵌提示词模板
└── tests/
    └── integration_test.rs # CLI + MCP 黑盒集成测试
```

## 关键模块

### `main.rs`

CLI 入口（clap 解析），支持 `mcp-server` 子命令。如果不在 tmux 内会自动重新进入 tmux。在 tokio 运行时启动之前先安装 panic 钩子，这样工作线程上的 panic 会被持久化到磁盘。

### `app.rs`

核心应用状态机。管理智能体列表、选中、聚焦、项目和 UI 状态。每个刷新 tick 都会重新从磁盘读取活动 EA、智能体、父子映射、worker 任务和项目列表，所以智能体通过 `omar mcp-server` 进行的更改无需额外的 IPC 通道就能在仪表盘里实时显示。

### `mcp.rs`

MCP stdio 服务器（约 2,800 行）。启动时读取 `McpLaunchContext`（omar 目录、EA id、会话前缀、默认 workdir、健康窗口、可选的 tmux server），并把所有工具调用都绑定在该上下文上。stdin/stdout 同时支持 Content-Length 与按行分隔两种分帧。`handle_tool_call` 中的工具分发覆盖 EA 管理、智能体、项目、调度、桌面操控、Slack 回复入队 —— 完整列表见 MCP 工具参考。

### `manager/mod.rs`

负责 EA 的 tmux 会话生命周期。针对每个后端写入相应的 MCP 集成产物：

- Claude：`~/.omar/mcp/ea-<id>/claude-mcp.json`，作为 `--mcp-config` 传入。
- Codex：`-c mcp_servers.omar.command=… -c mcp_servers.omar.args=…` 覆盖。
- Cursor：写入 `~/.cursor/mcp.json` 中的条目。
- Gemini：会话启动时执行 `gemini mcp add -s user omar …`。
- Opencode：用环境变量指向 `omar mcp-server --context-file …`。

同一模块还在 argv 层面下达后端原生唤醒 / 调度工具（`ScheduleWakeup`、`TaskReminder`、`task_reminder`、`scheduled_tasks`）的禁用规则，逼迫智能体始终走 OMAR 的持久化调度器。

### `scheduler/mod.rs`

事件调度系统使用 `BinaryHeap`（按时间戳的最小堆）。支持一次性事件与循环事件。**持久化** —— 每次变更都会原子地重写 `~/.omar/scheduled_events.json`，因此队列在重启后仍然存在。一把跨进程的有界文件锁（带过期 PID 回收）在仪表盘、管理器以及任何变更队列的 MCP 服务器子进程之间串行化写入。事件通过 `deliver_prompt` 注入到智能体的 tmux 会话（用 sentinel 包裹以兼容粘贴模式）。

### `ea.rs`

EA 注册表、id 分配（单调递增，永不复用）以及选择器解析。`resolve_or_create_ea_selector` 让 `--ea <name>` 在传入非数字名称且 EA 不存在时自动创建；不存在的数字 id 仍然报错，因为 id 是服务器分配的。

### `memory.rs` / `projects.rs`

按 EA 划分的快照与项目 CRUD。写入采用「临时文件 + rename」的原子方式，避免半路崩溃破坏文件。被内联进提示词之前会先做长度截断，以保持在 Linux 128 KB 的 `MAX_ARG_STRLEN` argv 上限之下。

## CLI 接口

```bash
# 启动仪表盘（默认行为，自动检测后端）
omar

# 指定智能体后端
omar --agent opencode

# 按名称自动创建并指定 EA
omar --ea Research

# 启动 MCP stdio 服务器（被派生的智能体和 Slack 桥接内部使用）
omar mcp-server --context-file ~/.omar/mcp/ea-0/context.json

# manager 子命令（仪表盘会自动启动它）
omar manager start

# 自定义配置
omar --config ~/.omar/config.toml
```

## 桥接

两个桥接都可选；当所需环境变量存在时会被自动启动：

- **Slack 桥接**（`omar-slack`）：当 `SLACK_BOT_TOKEN` 与 `SLACK_APP_TOKEN` 都设置时启动。它自己派生 `omar mcp-server` 子进程，通过 `schedule_omar_event` 工具把入站 Slack 消息送进 OMAR。回复经由 `slack_reply` 工具落到 `~/.omar/slack_outbox/`，桥接轮询该目录并通过 Slack Web API 发送。桥接的目标 EA 取自 `config.toml` 中的 `[slack_bridge].active_ea`，每次入站消息都会重新检查，因此仪表盘里的修改无需重启进程就会生效。
- **桌面操控桥接**（`omar-computer`）：在 `DISPLAY` 已设置时启动。提供 X11 鼠标 / 键盘 / 截屏控制，并按智能体维度做独占锁。

## 内嵌提示词

`/prompts/` 目录下的提示词被编译进二进制，并在首次运行时同步到 `~/.omar/prompts/`：

- `executive-assistant.md` —— EA 系统提示词（前面会拼接记忆与管理器笔记）
- `agent.md` —— 统一的智能体提示词（注入到所有派生的智能体）
- `watchdog.md` —— 可选的鉴权失败看门狗
- `prompts/tests/` —— 端到端测试场景（`project-factory.md`、`binary-tree-127-agents.md`、`flat-100-agents.md`）
- `prompts/demos/` —— 演示场景（`swarm-15.md`）

`{{EA_ID}}` / `{{EA_NAME}}` 占位符在启动时被替换 —— 对 Claude 来说会在 `--system-prompt-file` 读取之前先在磁盘上做替换；对内联提示词的后端则是在派生命令里通过 shell 展开完成替换。
