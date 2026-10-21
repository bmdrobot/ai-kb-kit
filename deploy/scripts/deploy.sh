#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CLAUDE_DIR="${HOME}/.claude"
CMD_DIR="${CLAUDE_DIR}/commands"
CONFIG_TARGET="${CLAUDE_DIR}/distill.config.md"

PYTHON_CMD="python"
if ! command -v python >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
  else
    echo "警告: 未找到 python/python3，请安装 Python 3.9+。" >&2
  fi
fi

mkdir -p "$CMD_DIR"
cp "$REPO_ROOT"/deploy/.claude/commands/*.md "$CMD_DIR"/

if [ -f "$CONFIG_TARGET" ]; then
  cp "$CONFIG_TARGET" "${CONFIG_TARGET}.bak"
fi

cat > "$CONFIG_TARGET" <<EOF
# 蒸馏配置

## 知识库本地路径
知识库路径：$REPO_ROOT

## Python 命令
Python命令：$PYTHON_CMD

## 说明
- 主题清单由仓库内的 topics/INDEX.md 自动维护。
- 新主题由 /distill 自动创建主题页。
- 重新部署：运行 deploy/scripts/deploy.sh。
EOF

echo "已同步命令到: $CMD_DIR"
echo "知识库路径: $REPO_ROOT"
echo "Python 命令: $PYTHON_CMD"
echo "配置: $CONFIG_TARGET"
echo "请重启 / 重载 Claude Code，让 /distill、/consolidate、/recall 生效。"
