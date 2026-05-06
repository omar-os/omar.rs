---
title: "MCP 工具参考"
description: "OMAR 通过 MCP stdio 暴露的工具表面：智能体编排、事件、桌面操控"
order: 4
---

## 概览

OMAR 通过 **MCP（Model Context Protocol）stdio 服务器** 对外暴露编排接口。每个智能体后端各自派生一个 `omar mcp-server` 子进程，并通过按行分隔的 JSON-RPC 与之对话。系统不监听端口、没有鉴权表面、也没有共享守护进程 —— 当智能体退出时，它的 MCP 子进程随之退出。

工具是类型化的，输入有 JSON-Schema 定义；从智能体视角看，每个工具都是 `omar.<tool_name>`。

### 智能体如何接入服务器

管理器把每个 EA 的 `McpLaunchContext` 写入 `~/.omar/mcp/ea-<id>/context.json`，并配置后端的 MCP 集成方式来启动：

```
omar mcp-server --context-file ~/.omar/mcp/ea-<id>/context.json
```

启动上下文里烤进了 EA id，因此该智能体的每次工具调用都自动绑定到它的 EA —— 无需逐次调用传 EA 路由参数，也不会发生跨 EA 的误操作。

## EA 注册表

| 工具             | 用途                                                                     |
| ---------------- | ------------------------------------------------------------------------ |
| `list_eas`       | 列出已注册的 EA，并标出 `is_active`（只读）。                            |
| `get_active_ea`  | 读取仪表盘 / CLI 默认使用的活动 EA 指针。                                |
| `switch_ea`      | 更新持久化的活动 EA 指针。**不会** 重定向当前 MCP 服务器 —— 已经在跑的子进程仍绑定到启动时的 EA。 |
| `create_ea`      | 按名称注册新的 EA（id 由服务器单调分配）。                               |
| `delete_ea`      | 注销 EA。会拒绝删除最后一个 EA 或仍有 attached 会话的 EA；文件系统错误会显式抛出而不是默默成功。 |

## 智能体

| 工具                  | 用途                                                                          |
| --------------------- | ----------------------------------------------------------------------------- |
| `list_agents`         | 列出当前 EA 中的活跃智能体，含健康状态与最近输出摘要。                        |
| `get_agent`           | 单个智能体的详细视图：窗格尾部、父智能体、状态、任务。                        |
| `get_agent_summary`   | 轻量卡片视图（健康、任务、状态、子智能体）。                                  |
| `update_agent_status` | 写入智能体的自报状态（持久化于 `~/.omar/ea/<id>/status/<session>.md`）。       |
| `spawn_agent`         | 唯一的派生入口。需要 `project_id`。返回该智能体的会话名。                     |
| `kill_agent`          | 杀死 tmux 会话，并把对应的 `Running` 任务行翻为 `Failed`。                    |
| `send_input`          | 向智能体的 tmux 会话注入文本（例如回应一次确认）。                            |

`spawn_agent` 参数：

```jsonc
{
  "name":       "auth",
  "task":       "实现 JWT 鉴权",
  "project_id": 1,
  "parent":     "ea",
  "workdir":    "/path/to/project",        // 可选，默认沿用启动 workdir
  "backend":    "codex",                   // 可选覆盖（claude/codex/cursor/gemini/opencode）
  "model":      "o3"                       // 可选 --model 覆盖
}
```

没有 `track` 标志；每次派生都会被追踪。`complete_task` 与 `replace_stuck_task_agent` 既接受短名（`auth`），也接受 UUID。

## 项目

| 工具               | 用途                                                                                            |
| ------------------ | ----------------------------------------------------------------------------------------------- |
| `list_projects`    | 列出当前 EA 的项目。                                                                            |
| `add_project`      | 注册一个项目桶；返回 `project_id` 用于 `spawn_agent`。                                          |
| `complete_project` | 移除项目。只要还有任务处于 `Running` 就会拒绝；`Failed`/`Replaced` 行作为历史记录保留。           |

## 事件 / 调度器

| 工具                  | 用途                                                                  |
| --------------------- | --------------------------------------------------------------------- |
| `schedule_omar_event` | 在 OMAR 的持久化调度器里入队一次性或循环事件。                        |
| `list_events`         | 查看当前 EA 的待处理事件。                                            |
| `cancel_event`        | 按 id 取消事件（仅当事件属于本 EA 时）。                              |

工具命名为 `schedule_omar_event` 以与其他 MCP 服务器发布的同名工具区分开 —— 凭直觉调用 `schedule_event` 会立刻报错，不会悄悄路由到别的服务器。

`schedule_omar_event` 参数：

```jsonc
{
  "receiver":          "auth",                      // 智能体短名，或填 "ea"
  "payload":           "auth 进度怎么样了？",
  "sender":            "ea",                        // 可选，默认 "ea"
  "delay_seconds":     300,                         // 5 分钟后唤醒
  "recurring_seconds": 300                          // 或：每 5 分钟自动重排
}
```

完成时立即唤醒父智能体，请用 `delay_seconds: 0`，payload 为 `"[CHILD COMPLETE] <你的名字>: <摘要>"`。

后端原生的唤醒工具（`ScheduleWakeup`、`TaskReminder`、`task_reminder`、`scheduled_tasks`）在派生层面通过 `--disallowedTools` 与各后端的 deny 配置直接禁用 —— 智能体必须使用 `schedule_omar_event`，这样唤醒事件才会出现在 OMAR 的事件队列里并能在重启后存活。

## 审计

| 工具                | 用途                                                                                                       |
| ------------------- | ---------------------------------------------------------------------------------------------------------- |
| `log_justification` | 在执行重要状态变更（派生、杀死、注入输入、调度、项目变更）之前，追加一条结构化 JSONL 审计记录。            |

## Slack

| 工具          | 用途                                                                                                  |
| ------------- | ----------------------------------------------------------------------------------------------------- |
| `slack_reply` | 把一份 Slack 回复文件入队到 `~/.omar/slack_outbox/`。Slack 桥接进程轮询该目录，再通过 Slack Web API 发送。 |

`slack_reply` 是唯一与 Slack 接触的工具 —— EA 永远不会直接和 Slack 对话。Slack 桥接是独立进程（`omar-slack`），其目标 EA 取自 `config.toml` 中的 `[slack_bridge].active_ea`。

## 桌面操控（Computer Use）

桌面操控接口持有一把独占锁，每次只允许一个智能体注入输入。所有桌面工具都要求智能体报上自己的名字以证明持锁身份。

| 工具                     | 用途                                                  |
| ------------------------ | ----------------------------------------------------- |
| `computer_status`        | 查询可用性与当前持锁者。                              |
| `computer_lock_acquire`  | 为指定智能体申请独占的桌面访问。                      |
| `computer_lock_release`  | 释放锁。                                              |
| `computer_screenshot`    | 截图（需要持锁）。                                    |
| `computer_mouse`         | `move`/`click`/`double_click`/`drag`/`scroll`。       |
| `computer_keyboard`      | `type` 输入文本，或 `key` 按下组合键。                |
| `computer_screen_size`   | 读取显示尺寸。                                        |
| `computer_mouse_position`| 读取当前鼠标位置。                                    |

## 后端探测

| 工具             | 用途                                                                                                                         |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `list_backends`  | 用有界的 `--version` 探测已安装的智能体后端（claude / codex / cursor / gemini / opencode）；适合在仪表盘或外部工具中列出可选项。 |

## 调用方视角

大多数智能体宿主都按工具名暴露 MCP 工具 —— 例如在 Claude Code 的工具盘里它们会显示为 `omar.spawn_agent`、`omar.schedule_omar_event` 等。直接对接 JSON-RPC 的客户端（如 Slack 桥接）按下面的方式调用：

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "tools/call",
  "params": {
    "name": "spawn_agent",
    "arguments": {
      "name": "auth",
      "task": "实现 JWT 鉴权",
      "project_id": 1
    }
  }
}
```

## 错误语义

- 工具级失败（未知智能体、attached 会话、参数校验拒绝）通过 `tools/call` 返回 `isError: true` 与单条文本内容块表达。
- JSON-RPC 的 `error` 仅承载协议级错误（JSON 解析失败、未知方法、消息分帧错误）。
- 工具是否可重试在 schema 描述中说明 —— 只读工具任何时候都可以重试；非幂等的变更工具（如 `add_project`）会建议在结果不确定时调用对应的 `list_*` 工具进行核对。

## 迁移说明

OMAR 0.3+ 取代了原有的 `:9876` REST API。如果有外部集成原本对接 `http://127.0.0.1:9876/api/...`，请改为派生 `omar mcp-server` 并通过 stdio 上的 JSON-RPC 调用工具 —— Slack 桥接（`bridges/slack/src/omar.rs`）是参考实现。
