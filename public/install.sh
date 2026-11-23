#!/bin/sh
# Runs install.sh from the latest omar-os/omar release, so this site never needs
# a copy and unreleased changes on main never reach users.
# The release comes from the /releases/latest redirect, not the rate-limited
# API, and is handed to install.sh so it installs that same release.
# Downloaded in full before running: a dropped connection can't run half of it.
# OMAR_VERSION and OMAR_INSTALL_DIR pass through the environment.
set -eu

REPO="omar-os/omar"

latest="$(curl -fsS -o /dev/null -w '%{redirect_url}' "https://github.com/$REPO/releases/latest")" || latest=""
TAG="${latest##*/}"
case "$TAG" in
  v*) ;;
  *) echo "Error: could not determine the latest omar release"; exit 1 ;;
esac

URL="https://raw.githubusercontent.com/$REPO/$TAG/install.sh"
script="$(curl -fsSL "$URL")" || {
  echo "Error: could not download $URL"
  exit 1
}
OMAR_VERSION="${OMAR_VERSION:-${TAG#v}}" exec sh -c "$script"
