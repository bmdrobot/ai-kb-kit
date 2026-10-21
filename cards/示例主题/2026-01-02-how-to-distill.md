---
id: 2026-01-02-how-to-distill
topic: 示例主题
title: 一次完整蒸馏的流程：从对话到卡片入库
type: 流程
tags: [知识库, 工作流, distill]
source: 实测
confidence: 高
created: 2026-01-02
review_after: 2026-07-02
status: active
last_used:
related: [2026-01-01-what-is-kb-kit]
---

# 一次完整蒸馏的流程：从对话到卡片入库

【核心知识点】蒸馏是"写"的动作：一次对话 → 提炼成一张原子卡片 → 更新主题页 → git 同步，全程一条命令搞定。

【通用方法/原则】
- 第 0 步：读配置 `~/.claude/distill.config.md` 与索引 `topics/INDEX.md`，先了解已有主题。
- 第 1 步：`git pull --rebase --autostash` 拉最新，避免覆盖他人/他机记录。
- 第 2 步：提炼——删寒暄与单次数值，归纳成通用方法，按 schema 填字段。
- 第 3 步：写入 `cards/<主题>/<日期>-<slug>.md`，运行 `validate` + `scan` 校验，再 `build` 重建索引。
- 第 4 步：`status` 确认范围 → 只 add 本次相关文件（禁止 `git add -A`）→ commit → 推送前再 pull → push。

【适用条件】刚结束一段有实质内容的 AI 对话，且认为其中有可复用的方法或教训。

【失效条件】对话全是寒暄、一次性调试、或纯信息查询（没有方法论可提炼）时不该沉淀。

【我的决策】优先沉淀「我的决策 + 证据」；纯 AI 通用知识应降低置信度，避免把模型已知内容当成个人经验。

【证据/结果（案例）】待补充
