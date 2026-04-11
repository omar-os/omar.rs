---
title: "智能体编排"
description: "OMAR 如何编排层级化智能体执行复杂任务"
order: 5
---

## 概览

OMAR 采用层级化智能体模型，由执行助理（EA）编排工作智能体。EA 将高层任务拆分为可并行的子任务，并创建智能体来执行。

## 统一智能体模型

除 EA 外，所有智能体使用相同的提示词（`agent.md`）。没有 PM/Worker 的区分 —— 每个创建的智能体都是自主的：接收任务后自行决定是直接完成还是创建子智能体，完成后报告结果。

EA（`executive-assistant.md`）比较特殊：它纯粹作为调度器 —— 从不直接工作，只负责创建智能体、监控进度和管理项目。它的提示词会前置记忆上下文。

## 智能体生命周期

```
用户向 EA 下达任务
        │
        ▼
EA 提出计划（JSON）
        │
        ▼
OMAR 解析计划，通过 API 创建智能体
        │
        ▼
  ┌─────────┐  ┌─────────┐  ┌─────────┐
  │ 智能体1 │  │ 智能体2 │  │ 智能体3 │
  │ 工作中  │  │ 工作中  │  │ 等待中  │
  └─────────┘  └─────────┘  └─────────┘
        │
        ▼
智能体通过 [TASK COMPLETE] 报告完成
        │
        ▼
EA 汇总结果
```

## 父子层级

智能体通过 `~/.omar/agent_parents.json` 追踪父节点。这使得：

- TUI 中的树形可视化（使用制表符绘制的命令树）
- 导航：`→/Tab` 深入子节点，`←` 返回父节点
- 层级化状态监控

任何智能体都可以创建子节点，支持任意深度。

## EA 协议

EA 完全通过 HTTP API 与 OMAR 通信。它从不直接执行工作 —— 只负责创建智能体、监控输出和管理项目。

### 创建智能体

```bash
curl -X POST http://localhost:9876/api/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "api", "task": "创建 Express 服务器，包含 /users 和 /posts 端点"}'
```

### 监控智能体

```bash
# 查看特定智能体的输出
curl http://localhost:9876/api/agents/api

# 列出所有智能体及健康状态
curl http://localhost:9876/api/agents
```

### 向智能体发送输入

```bash
curl -X POST http://localhost:9876/api/agents/api/send \
  -H "Content-Type: application/json" \
  -d '{"text": "也添加 /comments 端点", "enter": true}'
```

### 完成时终止智能体

```bash
curl -X DELETE http://localhost:9876/api/agents/api
```

### 管理项目

```bash
# 添加项目
curl -X POST http://localhost:9876/api/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "构建 REST API"}'

# 完成项目
curl -X DELETE http://localhost:9876/api/projects/<id>
```

## 智能体上下文

创建带任务的智能体时，OMAR 注入统一的 `agent.md` 提示词。每个智能体都是自主的 —— 自行决定是直接工作还是创建子智能体：

```
You are an Agent in the OMAR system.
You receive a task from your parent, assess it, and
decide the best way to get it done — either by doing
it yourself or by spawning sub-agents.

YOUR NAME: api
YOUR PARENT: ea
YOUR TASK: 创建 Express 服务器，包含 /users 和 /posts 端点
```

智能体通过输出 `[TASK COMPLETE]` 加上结果摘要来标记完成。

## 事件驱动协调

调度器支持智能体间的定时协调：

- **唤醒**：智能体调度自唤醒事件以检查子智能体进度
- **任务交接**：智能体 A 在依赖就绪时为智能体 B 调度事件
- **定时任务**：周期性事件在每次投递后自动重新调度

事件通过向目标智能体的 tmux 会话注入文本来投递。

```bash
# 调度一次性唤醒事件
curl -X POST http://localhost:9876/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "ea",
    "receiver": "api",
    "payload": "检查 API 实现进度",
    "timestamp": 1772904000000000000
  }'

# 调度周期性定时任务（每 5 分钟）
curl -X POST http://localhost:9876/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "ea",
    "receiver": "api",
    "payload": "进度检查",
    "recurring_ns": 300000000000
  }'
```

## 记忆持久化

OMAR 跨会话维护状态：

- **`~/.omar/memory.md`** —— 活跃项目、智能体和任务的快照
- **`~/.omar/worker_tasks.json`** —— 会话名到任务描述的映射
- **`~/.omar/agent_parents.json`** —— 父子关系
- **`~/.omar/status/<session>.md`** —— 智能体自报告状态

重启时，EA 提示词会包含上次的记忆快照以保持上下文连续性。
