---
title: "智能体编排"
description: "OMAR 如何编排层级化智能体执行复杂任务"
order: 5
---

## 概览

OMAR 采用层级化智能体模型。执行助理（EA）将高层任务拆分为可并行的子任务，并派生工作智能体 —— 每个智能体又可以派生自己的子智能体，从而构成任意深度的层级。每个智能体都通过自己专属的 `omar mcp-server` stdio 子进程暴露的 **MCP 工具表面** 来驱动 OMAR。

## 统一智能体模型

所有派生出来的智能体都使用同一份提示词（`agent.md`）。代码层面没有 PM/Worker 之分 —— 每个被派生的智能体都是自治的：它接到任务，决定亲自完成还是再派生子智能体，并在完成后报告。

执行助理（`executive-assistant.md`）则比较特殊：它纯粹作为调度者，从不亲自动手 —— 只派生智能体、监控它们、管理项目。它的提示词前会拼上记忆上下文。

## 智能体生命周期

```
用户向 EA 提交任务
        │
        ▼
EA 注册项目（add_project），并派生智能体（spawn_agent）
        │
        ▼
  agent-1（工作中）   agent-2（工作中）   agent-3（空闲）
        │
        ▼
智能体完成时通过 schedule_omar_event 唤醒父智能体
        │
        ▼
EA 汇总结果，完成后调用 complete_project
```

## 父子层级

智能体的父子关系记录在 `~/.omar/ea/<id>/agent_parents.json`。它带来：

- TUI 中的命令树可视化（带 box-drawing 字符）
- 导航：`↑/↓` 移动选中项，`←/→` 切换面板，`Tab` 钻入子智能体，`Shift+Tab` 返回父智能体
- 层级化的状态监控

任意智能体都可以派生子智能体，构成任意深度的层级。

## EA 协议

EA 与 OMAR 的所有交互都通过 MCP 工具调用完成。EA 永远不会亲自动手 —— 它只派生智能体、监控它们的输出、管理项目。下面以智能体在工具盘中看到的形式书写工具名（例如 `omar.spawn_agent`）。

### 注册项目

每次派生都需要 `project_id`，所以 EA 会先开一个项目再委派任务：

```jsonc
omar.add_project({ "name": "构建 REST API" })
// → { "project_id": 1, "name": "构建 REST API" }
```

### 派生智能体

```jsonc
omar.spawn_agent({
  "name":       "api",
  "task":       "搭建一个 Express 服务，提供 /users 与 /posts 接口",
  "project_id": 1,
  "parent":     "ea"
})
```

### 监控智能体

```jsonc
omar.list_agents()                         // → 当前 EA 中所有智能体及其健康状态
omar.get_agent({ "name": "api" })          // → 窗格尾部 + 状态 + 父智能体
omar.get_agent_summary({ "name": "api" })  // → 轻量卡片视图
```

### 向智能体发送输入

```jsonc
omar.send_input({
  "name": "api",
  "text": "再加一个 /comments 接口",
  "enter": true
})
```

### 杀死智能体

```jsonc
omar.kill_agent({ "name": "api" })
```

`kill_agent` 会把该智能体所有 `Running` 任务行翻为 `Failed` 并取消其已调度的事件，所以项目板上不会留下孤儿行。

### 管理项目

```jsonc
omar.list_projects()
omar.complete_project({ "project_id": 1 })   // 只要还有任务在 Running 就会拒绝
```

## 智能体上下文

派生带任务的智能体时，OMAR 会注入统一的 `agent.md` 提示词。每个智能体都是自治的 —— 自己决定是亲自完成还是再派生子智能体：

```
You are an Agent in the OMAR system.
You receive a task from your parent, assess it, and
decide the best way to get it done — either by doing
it yourself or by spawning sub-agents.

YOUR NAME: api
YOUR PARENT: ea
YOUR TASK: 搭建一个 Express 服务，提供 /users 与 /posts 接口
```

智能体通过输出 `[TASK COMPLETE]` 加一段总结来标记完成，并立刻唤醒父智能体：

```jsonc
omar.schedule_omar_event({
  "receiver":      "ea",
  "payload":       "[CHILD COMPLETE] api: 完成了 Express 服务，含 /users 与 /posts",
  "delay_seconds": 0
})
```

父智能体（EA 或别的智能体）会在自己的 tmux 会话里看到这条消息落地，然后据此进行汇总。

## 事件驱动协调

OMAR 的调度器是定时等待的唯一协调原语。后端原生的唤醒工具（`ScheduleWakeup`、`TaskReminder` 等）在派生层面就被禁用 —— 智能体必须使用 `schedule_omar_event`，这样唤醒事件才会出现在仪表盘的事件队列里并在重启后存活。

### 一次性唤醒

```jsonc
omar.schedule_omar_event({
  "receiver":      "api",
  "payload":       "检查一下 API 实现的进度",
  "delay_seconds": 60
})
```

### 周期性 cron 风格签到

```jsonc
omar.schedule_omar_event({
  "receiver":          "api",
  "payload":           "进度签到",
  "recurring_seconds": 300
})
```

事件是持久化的：会被写入 `~/.omar/scheduled_events.json`，仪表盘重启后仍会按时回放。事件的投递方式是把 payload 注入接收方的 tmux 会话。

## 记忆持久化

OMAR 在多次会话之间维持状态，按 EA 隔离：

- **`~/.omar/ea/<id>/memory.md`** —— 活动项目、智能体与任务的快照
- **`~/.omar/ea/<id>/worker_tasks.json`** —— 会话名 → 任务描述的映射
- **`~/.omar/ea/<id>/task_registry.json`** —— 权威任务记录（id、状态、历史）
- **`~/.omar/ea/<id>/agent_parents.json`** —— 父子关系
- **`~/.omar/ea/<id>/status/<session>.md`** —— 智能体自报状态
- **`~/.omar/manager_notes_ea<id>.md`** —— EA 通过 shell heredoc 写下的自由格式笔记
- **`~/.omar/scheduled_events.json`** —— 持久化事件队列（跨 EA 共享，按 `ea_id` 隔离）

重启时，EA 的提示词会带上最近的记忆快照以延续上下文，未触发的事件也会按计划继续触发。
