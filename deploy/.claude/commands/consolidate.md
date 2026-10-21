---
description: 把某个主题的活跃卡片归纳成通用方法论
argument-hint: <主题名>
---

# 归纳主题方法论

本次主题 = `$ARGUMENTS`；下文 `<主题>` 均指该值。

用法：`/consolidate <主题名>`；`$ARGUMENTS` 为空时，先读取 `topics/INDEX.md` 列出主题供用户选择，不要自行猜测。

## 第 0 步：读配置

读取 `.claude/distill.config.md`（先项目内后 `~/.claude/`），获取「知识库路径」和「Python命令」；未配置时用 `python`。下文记为 `<Python命令>`。

## 第 1 步：拉取最新

执行 `git -C "<知识库路径>" pull --rebase --autostash`；失败则停止并报告，不要自行解决冲突。

## 第 2 步：读取卡片

```bash
<Python命令> "<知识库路径>/deploy/scripts/kb.py" list "$ARGUMENTS" --status active
```

读取列出的每张卡片文件，以及该主题页现有的「通用方法论」「案例」。

若卡片的 `review_after` 已过，在归纳时标注「已过期，待复核」，不要直接当作当前事实。

## 第 3 步：归纳

写成一篇方法论笔记：

1. 通用流程：分阶段讲清「从零到完成」怎么走。
2. 每阶段用到的工具/库/方法。
3. 通用原则、常见坑、关键决策点。
4. 矛盾或证据不足的地方，单独列「未决分歧」，不要静默取一个。
5. 每个关键结论后用 `（来源：<卡片 id>）` 标注出处。
6. 文末「案例」：每个案例 2~3 句，说明如何套用流程；案例只作佐证。

## 第 4 步：更新主题页

- 用归纳结果覆盖 `topics/<主题>.md` 的「## 通用方法论」。
- 在方法论末尾加一行：`> 归纳于 YYYY-MM-DD，基于 N 张活跃卡片。`
- 覆盖「## 案例」。
- 标记卡片为已归纳：
  ```bash
  <Python命令> "<知识库路径>/deploy/scripts/kb.py" mark "$ARGUMENTS" --status consolidated
  ```
- 重新生成主题页：
  ```bash
  <Python命令> "<知识库路径>/deploy/scripts/kb.py" build --topic "$ARGUMENTS"
  ```

卡片会从「知识卡片流水」移动到「历史卡片（已归纳）」，链接保持可追溯。

## 第 5 步：提交并推送

- 执行 `git -C "<知识库路径>" status --short`，确认范围。
- 只暂存本次相关文件，禁止 `git add -A`：
  ```bash
  git -C "<知识库路径>" add -- "topics/<主题>.md" "topics/INDEX.md"
  git -C "<知识库路径>" add -- "cards/<主题>/<本次被 mark 的卡片>.md"
  ```
- 其他改动保持原样，不提交，并在报告中说明。
- `git -C "<知识库路径>" commit -m "consolidate: <主题>"`
- 推送前再同步一次：`git -C "<知识库路径>" pull --rebase --autostash`；失败则停止并报告。
- `git -C "<知识库路径>" push`；失败则报告用户，不强行处理。

## 最后报告

说明：归纳的主题、方法论要点、归档卡片数、是否推送成功；未提交的无关改动也一并说明。
