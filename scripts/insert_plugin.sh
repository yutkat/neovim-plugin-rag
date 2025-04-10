#!/bin/bash

if [ $# -ne 2 ]; then
  echo "Usage: $0 <GitHub URL> <file:line>"
  echo "Example: $0 https://github.com/yutkat/git-rebase-auto-diff.nvim /path/to/file.md:42"
  exit 1
fi

URL="$1"
FILE_LINE="$2"

PLUGIN="${URL#https://github.com/}"

FILE="${FILE_LINE%:*}"
LINE="${FILE_LINE##*:}"

sed -i "${LINE}i\\
- [${PLUGIN}](https://github.com/${PLUGIN}) ![](https://img.shields.io/github/stars/${PLUGIN}) ![](https://img.shields.io/github/last-commit/${PLUGIN}) ![](https://img.shields.io/github/commit-activity/y/${PLUGIN})
" "$FILE"

