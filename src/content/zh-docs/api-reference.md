---
title: "HTTP API 参考"
description: "OMAR 的 REST API —— 智能体编排、事件调度和桌面操控"
order: 4
---

## 概览

OMAR 在 9876 端口（可配置）运行 HTTP API，用于程序化管理智能体。任何能发 HTTP 请求的工具都可以编排智能体 —— Claude、opencode、Python 脚本、curl 等。

CORS 已全面启用（`Access-Control-Allow-Origin: *`）。

## 智能体端点

### `POST /api/agents`

创建新智能体。如果提供了 `task`，智能体会接收 `agent.md` 作为系统提示词并注入任务。

```json
// 请求
{
  "name": "worker-1",
  "task": "实现功能 X",
  "workdir": "/path/to/project",
  "command": "claude",
  "depends_on": ["worker-0"],
  "parent": "ea"
}

// 响应
{
  "id": "worker-1",
  "status": "running",
  "session": "omar-agent-worker-1",
  "created_at": "2025-01-26T12:00:00Z"
}
```

### `GET /api/agents`

列出所有智能体及其健康状态。

```json
{
  "agents": [
    {
      "id": "worker-1",
      "status": "running",
      "health": "working",
      "idle_seconds": 5,
      "last_output": "正在编写测试..."
    }
  ],
  "manager": {
    "id": "omar-agent-ea",
    "status": "running",
    "health": "working"
  }
}
```

### `GET /api/agents/:id`

获取智能体详情，包含最近的输出尾部。

### `GET /api/agents/:id/summary`

轻量级卡片视图：健康状态、任务、状态、子智能体。

### `PUT /api/agents/:id/status`

更新智能体的自报告状态（存储在 `~/.omar/status/<session>.md`）。

```json
{ "status": "正在实现认证模块 - 完成 60%" }
```

### `POST /api/agents/:id/send`

向智能体的 tmux 会话发送文本。

```json
{ "text": "好的，继续", "enter": true }
```

### `DELETE /api/agents/:id`

终止智能体会话。

**注意：** 会话名称同时接受短格式（`worker-1`）和完整格式（`omar-agent-worker-1`）。

## 事件端点

### `POST /api/events`

为智能体调度事件。

```json
{
  "sender": "ea",
  "receiver": "worker-1",
  "payload": "状态检查：实现进度如何？",
  "timestamp": 1772904000000000000,
  "recurring_ns": 300000000000
}
```

### `GET /api/events`

列出已调度的事件。支持 `?receiver=<name>` 查询过滤。

### `DELETE /api/events/:id`

取消已调度的事件。

## 项目端点

### `GET /api/projects`

列出 `~/.omar/tasks.md` 中的项目。

### `POST /api/projects`

添加新项目。

### `DELETE /api/projects/:id`

完成/移除项目。

## 桌面操控端点

### `GET /api/computer/status`

检查桌面操控是否可用，以及谁持有锁。

### `POST /api/computer/lock`

获取独占桌面访问权（同一时间只允许一个智能体）。

### `DELETE /api/computer/lock`

释放桌面锁。

### `POST /api/computer/screenshot`

截屏（需持有锁）。返回 base64 编码的图片。

### `POST /api/computer/mouse`

鼠标控制：移动、点击、拖拽、滚动。

### `POST /api/computer/keyboard`

键盘输入：输入文本或按组合键。

### `GET /api/computer/screen-size`

获取显示器分辨率。

### `GET /api/computer/mouse-position`

获取当前光标位置。

## 系统端点

### `GET /api/health`

健康检查。

```json
{ "status": "ok", "version": "0.1.0" }
```

## 配置

```toml
# ~/.config/omar/config.toml
[api]
enabled = true
port = 9876
host = "127.0.0.1"
```

## 使用示例

```bash
# 创建工作智能体
curl -X POST http://localhost:9876/api/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "auth", "task": "实现 JWT 认证", "parent": "ea"}'

# 查看状态
curl http://localhost:9876/api/agents/auth

# 发送输入
curl -X POST http://localhost:9876/api/agents/auth/send \
  -H "Content-Type: application/json" \
  -d '{"text": "y", "enter": true}'

# 调度周期性状态检查
curl -X POST http://localhost:9876/api/events \
  -H "Content-Type: application/json" \
  -d '{"sender": "ea", "receiver": "auth", "payload": "状态？", "recurring_ns": 300000000000}'

# 终止智能体
curl -X DELETE http://localhost:9876/api/agents/auth
```
