---
title: "Distribution"
description: "How to install and distribute OMAR across package managers"
order: 6
---

## Project Overview

OMAR is a Rust workspace with 3 crates:
- `omar` (main binary) - the TUI dashboard
- `omar-slack-bridge` - Slack bridge binary
- `omar-computer-bridge` - computer-use bridge binary

Runtime dependency: **tmux 3.0+**

## Installation Methods

### Build from Source (Recommended)

```bash
git clone https://github.com/lsk567/omar.git
cd omar
make install
```

### cargo install

```bash
cargo install omar
```

### Homebrew (macOS)

```bash
brew tap lsk567/tap
brew install omar
```

## Distribution Priority

| Priority | Platform | Reach | Notes |
|----------|----------|-------|-------|
| 1 | GitHub Releases | High | Foundation for everything else |
| 2 | cargo install (crates.io) | High (Rust users) | Trivial once metadata is ready |
| 3 | Homebrew tap | High (macOS) | Uses GitHub Release binaries |
| 4 | AUR | Medium (Arch) | Community may create this |
| 5 | Nix | Medium | Growing community |
| 6 | npm wrapper | Low | Only if targeting JS developers |

## GitHub Releases

Pre-built binaries for all major platforms are provided via GitHub Releases with automated cross-compilation:

- `x86_64-unknown-linux-gnu`
- `aarch64-unknown-linux-gnu`
- `x86_64-apple-darwin`
- `aarch64-apple-darwin`

Each release includes `sha256sums.txt` for verification.

### Creating a Release

```bash
git tag v0.1.0
git push origin v0.1.0
```

The CI workflow builds binaries for all targets and creates a GitHub Release automatically.

## AUR (Arch Linux)

Available as `omar-bin` (pre-built binary) and `omar` (build from source).

```bash
# Using an AUR helper
yay -S omar-bin
```

## Nix

```bash
nix profile install github:lsk567/omar
# or run directly
nix run github:lsk567/omar
```

## Docker

```bash
docker run --rm -it -v $(pwd):/workspace lsk567/omar
```

> Note: OMAR manages tmux sessions on the host, so Docker adds friction. Build from source is preferred.
