---
title: "智能体编排"
description: "OMAR 如何编排层级化智能体执行复杂任务"
order: 5
---

## 概览

OMAR 采用层级化智能体模型，由执行助理（EA）编排工作智能体。EA 将高层任务拆分为可并行的子任务，并创建智能体来执行。

## 统一智能体模型

除 EA 外，所有智能体使用相同的角色和提示词（`agent.md`）。没有 PM/Worker 的区分 —— 每个创建的智能体都是平等的，接收任务后独立工作。

EA（`executive-assistant.md`）比较特殊：它的提示词会前置记忆上下文，包括活跃项目、运行中的智能体及其任务。

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

EA 通过其输出中的结构化 JSON 与 OMAR 通信：

### 创建智能体

```json
{
  "type": "plan",
  "agents": [
    {
      "name": "api",
      "role": "API 开发者",
      "task": "创建 Express 服务器，包含 /users 和 /posts 端点",
      "depends_on": []
    }
  ]
}
```

### 向智能体发消息

```json
{
  "type": "send",
  "target": "api",
  "message": "也添加 /comments 端点"
}
```

### 查询状态

```json
{
  "type": "query",
  "target": "all"
}
```

### 标记完成

```json
{
  "type": "complete"
}
```

## 工作智能体上下文

创建带任务的智能体时，OMAR 注入统一的 `agent.md` 提示词和上下文：

```
你是多智能体项目中的一个工作智能体。

你的任务：创建 Express 服务器，包含 /users 和 /posts 端点

注意事项：
- 专注于你被分配的任务
- 完成时以 [TASK COMPLETE] 结尾
- 如果被阻塞，说：[BLOCKED: 原因]
- 如果需要输入，说：[NEED INPUT: 问题]
```

## 事件驱动协调

调度器支持智能体间的定时协调：

- **状态检查**：EA 调度周期性事件来轮询工作智能体
- **任务交接**：智能体 A 在依赖就绪时为智能体 B 调度事件
- **提醒**：智能体可以为自己设置未来事件

事件通过向目标智能体的 tmux 会话注入文本来投递。

```bash
# 调度每 5 分钟一次的周期性状态检查
curl -X POST http://localhost:9876/api/events \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "ea",
    "receiver": "api",
    "payload": "[STATUS CHECK] 报告你的进度",
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
