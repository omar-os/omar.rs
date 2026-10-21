#!/bin/sh
# Runs install.sh from omar-os/omar main, so this site never needs a copy.
# Downloaded in full before running: a dropped connection can't run half of it.
# OMAR_VERSION and OMAR_INSTALL_DIR pass through the environment.
set -eu

URL="https://raw.githubusercontent.com/omar-os/omar/main/install.sh"

script="$(curl -fsSL "$URL")" || {
  echo "Error: could not download $URL"
  exit 1
}
exec sh -c "$script"
