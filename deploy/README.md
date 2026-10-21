# AI 知识蒸馏 · 部署与使用

把和 Claude 的对话 **筛选 → 提炼 → 归纳** 成原子知识卡片，并用检索命令反哺后续任务。

## 一、前置条件

| 依赖 | 要求 | 说明 |
|---|---|---|
| Git | 2.6+ | 需要 `pull --rebase --autostash` |
| Python | 3.9+ | `kb.py` 只依赖标准库 |
| Claude Code | CLI 或 VSCode 扩展 | 支持自定义斜杠命令 |
| 仓库 | 私有 Git 仓库 | 已 clone 到本机 |

Windows 通常使用 `python`；macOS / Linux 可能是 `python3`。部署脚本会自动检测并写入配置，命令会读取 `Python命令` 字段。

## 二、首次部署（新设备）

1. 克隆仓库：

   ```bash
   git clone https://gitee.com/sun-qingyao/ai_study_record.git
   cd ai_study_record
   ```

2. 一键部署：

   - Windows：
     ```powershell
     powershell -ExecutionPolicy Bypass -File deploy/scripts/deploy.ps1
     ```
   - macOS / Linux：
     ```bash
     bash deploy/scripts/deploy.sh
     ```

   脚本会：
   - 把 `deploy/.claude/commands/` 下的 `/distill`、`/consolidate`、`/recall` 复制到 `~/.claude/commands/`；
   - 生成/更新 `~/.claude/distill.config.md`，自动写入本机仓库路径和 Python 命令；
   - 旧配置备份为 `distill.config.md.bak`。

3. **重启 / 重载 Claude Code**，让新命令生效。
   - VSCode：`Ctrl+Shift+P` → `Developer: Reload Window`
   - 或直接重启 Claude Code 会话

4. 按下一节做自检。

## 三、部署后自检

### 1. 命令文件存在

- Windows：`Get-ChildItem $env:USERPROFILE\.claude\commands`
- macOS / Linux：`ls ~/.claude/commands`

应看到 `distill.md`、`consolidate.md`、`recall.md`。

### 2. 配置正确

打开 `~/.claude/distill.config.md`，确认：

```markdown
## 知识库本地路径
知识库路径：<本机仓库路径>

## Python 命令
Python命令：python
```

### 3. 工具链可运行

在仓库根目录执行（`<Python命令>` 换成 `python` 或 `python3`）：

```bash
<Python命令> deploy/scripts/kb.py validate
<Python命令> deploy/scripts/kb.py scan
<Python命令> deploy/scripts/kb.py build
<Python命令> deploy/scripts/kb.py recall "RL"
```

预期：校验通过、扫描通过、主题页/索引更新、检索命中 RL 卡片。

### 4. 命令可用

重启后输入：

```text
/recall RL
```

应返回卡片摘要和方法论路径。若提示命令不存在，说明会话还没重载。

## 四、使用示例

### 示例 1：蒸馏一段对话

输入：

```text
/distill
```

它会：

1. 从当前对话提炼一张原子卡片；
2. 写入 `cards/<主题>/<日期>-<slug>.md`；
3. 运行 `validate` + `scan`；
4. 更新 `topics/<主题>.md` 和 `topics/INDEX.md`；
5. 只提交本次相关文件，commit 形如 `distill: RL学习路线 - RL 初学者学习路线`。

卡片文件示例：

```markdown
---
id: 2026-10-19-rl-learning-path
topic: RL学习路线
title: RL 初学者学习路线
type: 流程
tags: [RL, 学习路线, 入门]
source: AI建议
confidence: 中
created: 2026-10-19
review_after: 2027-04-19
status: active
---

# RL 初学者学习路线

【核心知识点】...
【通用方法/原则】
- ...
【适用条件】...
【失效条件】...
【我的决策】...
【证据/结果（案例）】...
```

优先沉淀「我的决策 + 证据」；纯 AI 通用知识会降低置信度。

### 示例 2：检索已有沉淀

输入：

```text
/recall RL
```

预期输出：

```text
查询: RL
索引: topics/INDEX.md
命中 1 张卡片:

[1] 2026-10-19 | RL 初学者学习路线
    主题: RL学习路线 | 类型: 流程 | 来源: AI建议 | 置信度: 中 | 状态: active
    核心: RL 初学者应按「前置基础 → 经典 RL → 深度 RL → 方向专精」四阶段递进...
    卡片: cards/RL学习路线/2026-10-19-rl-learning-path.md
    方法论: topics/RL学习路线.md
```

随后 Claude 会读取卡片和主题页，总结适用条件、失效条件，并提醒置信度和复核日期。

### 示例 3：归纳主题方法论

输入：

```text
/consolidate RL学习路线
```

前提：该主题至少有一张 `active` 卡片，建议积累 5~10 张后再做。

它会：

- 读取全部活跃卡片；
- 写入/覆盖主题页的「通用方法论」和「案例」；
- 关键结论标注来源卡片 id；
- 矛盾单独列为「未决分歧」；
- 把卡片状态改为 `consolidated`，移入「历史卡片（已归纳）」；
- commit 形如 `consolidate: RL学习路线`。

卡片不会删除，归档后仍可追溯。

### 示例 4：直接使用工具

```bash
<Python命令> deploy/scripts/kb.py build [--topic 主题]       # 重建主题页卡片区与索引
<Python命令> deploy/scripts/kb.py recall "关键词" --limit 5  # 检索
<Python命令> deploy/scripts/kb.py validate [卡片路径 ...]    # 校验 schema
<Python命令> deploy/scripts/kb.py scan [卡片路径 ...]        # 扫描常见密钥
<Python命令> deploy/scripts/kb.py list 主题 --status active  # 列卡片
<Python命令> deploy/scripts/kb.py mark 主题 --status consolidated  # 归档
```

## 五、日常使用

| 时机 | 命令 | 效果 |
|---|---|---|
| 聊完一个有价值主题 | `/distill` | 生成原子卡片 + 更新主题页/索引 + git 同步 |
| 开始一个新任务 | `/recall <关键词>` | 检索相关卡片和方法论 |
| 某主题攒够 5~10 张卡片 | `/consolidate <主题>` | 归纳成通用方法论，卡片归档 |

## 六、多设备同步

每台设备 clone 同一个仓库，运行一次部署脚本即可。命令执行前 `git pull --rebase`，写入后 `git push`；
一卡一文件的设计把冲突面降到最低。

## 七、知识库结构

```text
ai_study_record/
├── cards/<主题>/<日期>-<slug>.md   # 原子卡片
├── topics/
│   ├── INDEX.md                    # 自动生成的索引
│   └── <主题>.md                   # 方法论 + 卡片流水
├── deploy/
│   ├── .claude/commands/           # /distill /consolidate /recall
│   ├── .claude/distill.config.md   # 配置模板
│   └── scripts/                    # kb.py + 一键部署脚本
└── README.md
```

## 八、检索闭环

知识库只有被读才有复利。推荐在常用项目的 `CLAUDE.md` 中加入：

```markdown
## 个人知识库
索引：<仓库路径>/topics/INDEX.md
涉及已有主题时，先运行 `/recall <关键词>` 或读取对应主题页。
```

这一步不配也能用 `/recall`，但配了之后 Claude 会在任务开始时主动看索引。

## 九、常见问题

- **`/recall` 不出现，或加载的是旧版本**：新加/修改的命令不会热更新，重启或重载 Claude Code。
- **找不到 `python`**：改用 `python3`；重新运行部署脚本会自动检测并写入配置。
- **`/distill` 提示 pull 失败**：先处理工作区的未提交改动；命令不会强推，也不会自动丢改动。
- **当前项目里有 `.claude/distill.config.md`**：项目级配置优先于 `~/.claude/`；确认它指向本仓库，或删除它。
- **push 失败**：先 `git pull --rebase --autostash`；有冲突就手动解决，不要强推。
- **`scan` 命中**：人工确认是否含密钥；脱敏后重新运行，不要直接提交。
- **想改主题页**：「通用方法论」「案例」可以手改；`<!-- cards:... -->` 标记之间由 `build` 生成，不要手改。

## 十、隐私

- 使用私有仓库。
- `/distill` 提交前运行 `scan`；命中时人工确认，不要自动删除证据。
- 对话中不要粘贴生产密钥、客户隐私数据；脱敏后再沉淀。
