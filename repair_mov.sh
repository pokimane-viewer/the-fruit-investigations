#!/usr/bin/env bash
set -euo pipefail

if ! command -v brew >/dev/null; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

brew update
brew install ffmpeg yasm pkg-config

git clone https://github.com/anthwlock/untrunc.git
cd untrunc

export PKG_CONFIG_PATH="$(brew --prefix)/lib/pkgconfig"
CPPFLAGS="-I$(brew --prefix)/include" LDFLAGS="-L$(brew --prefix)/lib" make

sudo cp untrunc /usr/local/bin