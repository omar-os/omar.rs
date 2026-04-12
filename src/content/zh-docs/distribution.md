---
title: "安装与分发"
description: "如何安装 OMAR 以及各包管理器的分发方式"
order: 6
---

## 项目概览

OMAR 是一个 Rust 工作区，包含 3 个二进制：

- `omar` —— TUI 仪表盘
- `omar-slack` —— Slack 桥接
- `omar-computer` —— 桌面操控桥接

运行依赖：**tmux 3.0+**

## 安装方式

### 一键安装（推荐）

```bash
curl -fsSL https://omar.tech/install.sh | sh
```

自动检测操作系统（macOS/Linux）和架构（amd64/arm64），将 3 个二进制安装到 `/usr/local/bin`。

选项：

```bash
# 指定版本
OMAR_VERSION=0.1.0 curl -fsSL https://omar.tech/install.sh | sh

# 自定义安装目录
OMAR_INSTALL_DIR=~/.local/bin curl -fsSL https://omar.tech/install.sh | sh
```

### Homebrew

```bash
brew install lsk567/omar/omar
```

自动安装 tmux 依赖。

### 从源码编译

```bash
git clone https://github.com/lsk567/omar.git
cd omar
make install
```

需要 Rust 1.70+ 和 GNU Make。

## GitHub Releases

通过 [GitHub Releases](https://github.com/lsk567/omar/releases) 提供所有主流平台的预编译二进制：

- `omar-linux-amd64.tar.gz`
- `omar-linux-arm64.tar.gz`
- `omar-darwin-amd64.tar.gz`
- `omar-darwin-arm64.tar.gz`

每个版本包含 `checksums.txt`（SHA256）用于校验。

### 创建发布

```bash
git tag v0.1.0
git push origin v0.1.0
```

CI 工作流会自动为所有目标构建二进制、创建 GitHub Release，并自动更新 Homebrew formula。
