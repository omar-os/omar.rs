---
title: "Distribution"
description: "How to install and distribute OMAR across package managers"
order: 6
---

## Project Overview

OMAR is a Rust workspace with 3 binaries:

- `omar` — the TUI dashboard
- `omar-slack` — Slack bridge
- `omar-computer` — computer-use bridge

Runtime dependency: **tmux 3.0+**

## Installation Methods

### One-Liner (Recommended)

```bash
curl -fsSL https://omar.tech/install.sh | sh
```

Auto-detects OS (macOS/Linux) and architecture (amd64/arm64). Installs all 3 binaries to `/usr/local/bin`.

Options:

```bash
# Pin a specific version
OMAR_VERSION=0.2.2 curl -fsSL https://omar.tech/install.sh | sh

# Custom install directory
OMAR_INSTALL_DIR=~/.local/bin curl -fsSL https://omar.tech/install.sh | sh
```

### Homebrew

```bash
brew install lsk567/omar/omar
```

Automatically installs tmux as a dependency.

### From Source

```bash
git clone https://github.com/lsk567/omar.git
cd omar
make install
```

Requires Rust 1.70+ and GNU Make.

## GitHub Releases

Pre-built binaries for all major platforms are provided via [GitHub Releases](https://github.com/lsk567/omar/releases):

- `omar-linux-amd64.tar.gz`
- `omar-linux-arm64.tar.gz`
- `omar-darwin-amd64.tar.gz`
- `omar-darwin-arm64.tar.gz`

Each release includes `checksums.txt` (SHA256) for verification.
