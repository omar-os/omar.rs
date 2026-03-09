---
title: "安装与分发"
description: "如何安装 OMAR 以及各包管理器的分发方式"
order: 6
---

## 项目概览

OMAR 是一个 Rust 工作区，包含 3 个 crate：

- `omar`（主程序）—— TUI 仪表盘
- `omar-slack-bridge` —— Slack 桥接
- `omar-computer-bridge` —— 桌面操控桥接

运行依赖：**tmux 3.0+**

## 安装方式

### 从源码构建（推荐）

```bash
git clone https://github.com/lsk567/omar.git
cd omar
make install
```

### cargo install

```bash
cargo install omar
```

### Homebrew（macOS）

```bash
brew tap lsk567/tap
brew install omar
```

## 分发优先级

| 优先级 | 平台                       | 覆盖范围        | 备注                       |
| ------ | -------------------------- | --------------- | -------------------------- |
| 1      | GitHub Releases            | 广              | 其他渠道的基础             |
| 2      | cargo install（crates.io） | 广（Rust 用户） | 元数据就绪后即可发布       |
| 3      | Homebrew tap               | 广（macOS）     | 使用 GitHub Release 二进制 |
| 4      | AUR                        | 中等（Arch）    | 社区可能会创建             |
| 5      | Nix                        | 中等            | 社区持续增长               |
| 6      | npm 封装                   | 低              | 仅在面向 JS 开发者时考虑   |

## GitHub Releases

通过 GitHub Releases 提供所有主流平台的预编译二进制，支持自动交叉编译：

- `x86_64-unknown-linux-gnu`
- `aarch64-unknown-linux-gnu`
- `x86_64-apple-darwin`
- `aarch64-apple-darwin`

每个版本包含 `sha256sums.txt` 用于校验。

### 创建发布

```bash
git tag v0.1.0
git push origin v0.1.0
```

CI 工作流会自动为所有目标构建二进制并创建 GitHub Release。

## AUR（Arch Linux）

提供 `omar-bin`（预编译二进制）和 `omar`（从源码构建）两种方式。

```bash
# 使用 AUR 助手
yay -S omar-bin
```

## Nix

```bash
nix profile install github:lsk567/omar
# 或直接运行
nix run github:lsk567/omar
```

## Docker

```bash
docker run --rm -it -v $(pwd):/workspace lsk567/omar
```

> 注意：OMAR 管理的是宿主机上的 tmux 会话，Docker 会增加额外复杂度。推荐从源码构建。
