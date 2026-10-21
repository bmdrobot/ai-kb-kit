# ai-kb-kit

> 把和 AI 的对话，蒸馏成可检索、可复核的方法论知识库。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 你有没有这种感觉

问了 AI 一百个问题，回头一个都想不起来。

- 同一个坑，踩了三次，每次都重新问一遍 AI；
- 对话散落在网页端、客户端、不同的电脑里，根本翻不到；
- 就算翻到了，也是一堆流水账，找不到"当时到底是怎么解决的"。

**信息进来了，但没沉淀下来。**

`ai-kb-kit` 就是为解决这件事而做的：让你每一次有价值的对话，都变成可复用、可检索、能长期积累的资产。

---

## 它做了什么

把你和 AI 的对话，**自动蒸馏成结构化的知识卡片**，并能在需要时检索回来。

```
      对话
       ↓  /distill
  原子卡片 + 主题页 + 索引
       ↓
   新任务  →  /recall  →  方法论 + 案例
       ↓
 积累 5~10 张  →  /consolidate  →  通用方法论（带来源引用）
```

**关键区别**：多数人的知识库是"只进不出的档案"；这套系统有**读写闭环**——`/distill` 负责写，`/recall` 负责读。

### 三个命令

| 命令 | 作用 | 何时用 |
|---|---|---|
| **`/distill`** | 把当前对话蒸馏成一张知识卡片，写入知识库 + git 同步 | 聊完有价值内容 |
| **`/recall <关键词>`** | 检索已有沉淀，把方法论用到当前任务 | **新任务开始前** |
| **`/consolidate <主题>`** | 把同主题卡片归纳成通用方法论 | 某主题攒够卡片 |

---

## 效果一览

### 1) 沉淀：一次对话 → 一张卡片

聊完有价值内容后输入：

```
/distill
```

自动写入 `cards/<主题>/<日期>-<slug>.md`，并重建索引与主题页：

```
$ python deploy/scripts/kb.py build
校验通过：3 张卡片

[新建] topics\示例主题.md
[更新] topics\示例主题.md: active=3, archived=0
[更新] topics\INDEX.md: 1 个主题
```

生成的 `topics/INDEX.md` 长这样：

```
| 主题 | 说明 | 活跃卡片 | 最近更新 |
|---|---|---:|---|
| [示例主题](示例主题.md) | 一句话说明解决什么问题 | 3 | 2026-01-03 |
```

### 2) 复用：新任务开始前检索

下次遇到同类问题，先检索：

```
$ python deploy/scripts/kb.py recall 实时线程 卡顿
命中 1 张卡片:
[1] 2026-10-21 | 实时线程长时间停顿时按「调度/阻塞/缺页」三分法定位
    主题: 实时线程排障 | 类型: 流程 | 来源: 混合 | 置信度: 中 | 状态: active
    核心: RT 线程出现数百毫秒级停顿，先区分"线程没被调度"与"线程被卡住"…
    卡片: cards/实时线程排障/2026-10-21-rt-thread-stall-triage.md
    方法论: topics/实时线程排障.md
```

> 以上是真实运行输出，非示意。

---

## 和同类方案的区别

| | 对话导出工具 | 笔记软件 + git | Agent 记忆库 | **本方案** |
|---|---|---|---|---|
| 保存原始对话 | ✓ | 手动整理 | ✓ | 提炼后存卡片 |
| 提炼成通用方法论 | ✗ | 靠自觉 | 部分支持 | ✓ `/consolidate` |
| 来源 / 置信度标注 | ✗ | ✗ | 部分支持 | ✓ schema 强制 |
| 主动检索复用 | ✗ | ✗ | 自动注入 | ✓ `/recall` |
| 多机自动汇总 | ✗ | 手动同步 | ✗ | ✓ git pull/push |
| 零第三方依赖 | 视实现 | ✓ | ✗ | ✓ 仅标准库 |

**核心差异：多数工具解决的是"存下来"，本方案解决的是"沉淀成方法论，并能在需要时检索回来用"。**

---

## 快速开始

前置条件：
- Git 2.6+
- Python 3.9+
- [Claude Code](https://claude.com/claude-code)

### 1. 克隆并部署

```bash
git clone https://github.com/<你的用户名>/ai-kb-kit.git
cd ai-kb-kit
```

Windows（PowerShell）：
```powershell
powershell -ExecutionPolicy Bypass -File deploy/scripts/deploy.ps1
```

macOS / Linux：
```bash
bash deploy/scripts/deploy.sh
```

部署脚本会：
- 提示你输入**知识库本地路径**
- 把三个斜杠命令装到全局目录 `~/.claude/commands/`
- 生成本机配置 `~/.claude/distill.config.md`

### 2. 开始用

重启 / 重载 Claude Code 后：

```
/distill                      # 聊完有价值内容，一键入库
/recall 关键词                # 新任务开始前，先检索
/consolidate 主题名           # 攒够卡片后，归纳成方法论
```

> 新增或修改斜杠命令后，需要重启 / 重载 Claude Code 才会生效。

---

## 目录结构

```
ai-kb-kit/
├── cards/          原子知识卡片，一卡一文件，带 frontmatter
│   └── <主题>/
│       └── <YYYY-MM-DD>-<slug>.md
├── topics/         主题页 + 索引
│   ├── INDEX.md            自动生成的主题索引
│   └── <主题>.md           通用方法论 + 案例 + 卡片流水
└── deploy/         命令、配置、脚本与部署说明
    ├── README.md
    ├── scripts/
    │   ├── deploy.ps1
    │   ├── deploy.sh
    │   └── kb.py
    └── .claude/
        ├── distill.config.md
        └── commands/
            ├── distill.md
            ├── consolidate.md
            └── recall.md
```

---

## 卡片 schema

```yaml
---
id: 2026-10-19-example-topic
topic: 示例主题
title: 一句话标题
type: 流程              # 流程 / 原则 / 坑 / 决策 / 参考
tags: [标签1, 标签2]
source: AI建议          # AI建议 / 实测 / 论文 / 他人经验 / 混合
confidence: 中          # 高 / 中 / 低
created: 2026-10-19
review_after: 2027-04-19
status: active          # active / consolidated / archived
last_used:
related: []
---
```

正文固定包含 6 段：**核心知识点 / 通用方法·原则 / 适用条件 / 失效条件 / 我的决策 / 证据·结果**。

---

## 设计原则

- **蒸馏而非存储**：只留可复用方法，同时保留来源与证据。
- **方法论优先**：通用流程/原则在前，案例只作佐证。
- **原子卡片**：一卡一文件，减少 git 冲突，便于检索、引用、归档。
- **可追溯**：结论标注来源卡片；`/consolidate` 不删证据。
- **可复核**：每张卡带 `review_after`，过期内容在归纳时标注待复核。
- **读写闭环**：`/distill` 写、`/recall` 读，避免知识库变成只进不出的档案。

---

## 工具脚本

`deploy/scripts/kb.py` 是唯一的辅助脚本，**零第三方依赖**（只用 Python 标准库）：

| 子命令 | 作用 |
|---|---|
| `build` | 重建主题页卡片区 + 主题索引 |
| `validate` | 校验卡片 schema（字段、取值、日期、目录一致性） |
| `scan` | 扫描常见密钥模式，防止误提交 |
| `recall` | 按关键词检索卡片（含置信度/新近度加权） |
| `list` | 列出某主题的卡片 |
| `mark` | 批量更新卡片状态 |

---

## 隐私

- **建议使用私有仓库**存放你的真实笔记。
- `/distill` 在提交前会运行 `kb.py scan` 检查常见密钥模式；命中时需人工确认，不会自动删除内容。
- 不要在和 AI 的对话中粘贴生产密钥、客户隐私数据；脱敏后再沉淀。

---

## License

MIT
