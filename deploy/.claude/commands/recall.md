---
description: 从个人知识库检索与当前任务相关的卡片和方法论
argument-hint: <关键词或主题>
---

# 检索知识库

本次查询 = `$ARGUMENTS`；下文 `<关键词>` 均指该值。

## 第 0 步：读配置

读取 `.claude/distill.config.md`（先项目内后 `~/.claude/`），获取「知识库路径」和「Python命令」；未配置时用 `python`。下文记为 `<Python命令>`。

## 第 1 步：检索

```bash
<Python命令> "<知识库路径>/deploy/scripts/kb.py" recall "$ARGUMENTS" --limit 5
```

- 若 `$ARGUMENTS` 为空，先询问用户要检索什么，不要自行猜测。
- 需要包含已归纳卡片时，加 `--include-consolidated`。

## 第 2 步：阅读

读取命中的卡片文件；如果存在对应主题页，同时读取其「## 通用方法论」。

## 第 3 步：应用

- 先用 2~3 句话总结命中的方法论/原则；
- 明确说明适用条件和失效条件；
- 如果知识库内容与当前任务冲突，指出冲突，不要生搬硬套；
- 注意卡片的 `source`、`confidence` 和 `review_after`，不要把低置信度过期内容当成事实；
- 只读，不要修改知识库。
