#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""个人知识库工具（仅依赖 Python 标准库）。

用法：
  python deploy/scripts/kb.py build [--topic TOPIC]
  python deploy/scripts/kb.py recall <query> [--limit 5] [--include-consolidated]
  python deploy/scripts/kb.py validate [path ...]
  python deploy/scripts/kb.py scan [path ...]
  python deploy/scripts/kb.py list <topic> [--status active]
  python deploy/scripts/kb.py mark <topic> --status consolidated [--ids id1,id2]

约定：
  cards/<topic>/<YYYY-MM-DD>-<slug>.md   原子卡片
  topics/<topic>.md                      主题页（卡片区由 build 生成）
  topics/INDEX.md                        主题索引（由 build 生成）
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

if sys.version_info < (3, 9):
    raise SystemExit("kb.py 需要 Python 3.9+")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
CARDS = ROOT / "cards"
TOPICS = ROOT / "topics"
INDEX = TOPICS / "INDEX.md"

ACTIVE_START = "<!-- cards:active:start -->"
ACTIVE_END = "<!-- cards:active:end -->"
ARCHIVE_START = "<!-- cards:archived:start -->"
ARCHIVE_END = "<!-- cards:archived:end -->"

REQUIRED = ["id", "topic", "title", "type", "tags", "source", "confidence", "created", "status"]
ALLOWED = {
    "type": {"流程", "原则", "坑", "决策", "参考"},
    "source": {"AI建议", "实测", "论文", "他人经验", "混合"},
    "confidence": {"高", "中", "低"},
    "status": {"active", "consolidated", "archived"},
}

SECRET_PATTERNS = [
    ("OpenAI/Anthropic key", r"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}\b"),
    ("AWS Access Key", r"\bAKIA[0-9A-Z]{16}\b"),
    ("GitHub token", r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    ("Slack token", r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    ("Google API key", r"\bAIza[0-9A-Za-z_-]{35}\b"),
    ("Private key", r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    (
        "Generic secret",
        r"(?i)\b(?:password|passwd|secret|api[_-]?key|access[_-]?token)\b\s*[:=]\s*['\"]?[^\s'\"]{8,}",
    ),
]


class CardError(Exception):
    pass


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_value(value: str):
    value = value.strip()
    if value == "" or value.lower() in ("null", "none", "~"):
        return None
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [unquote(item) for item in inner.split(",") if item.strip()]
    return unquote(value)


def split_frontmatter(text: str):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise CardError("文件开头不是 YAML frontmatter（---）")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise CardError("frontmatter 没有结束标记 ---")
    meta = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise CardError(f"frontmatter 行无法解析: {line}")
        key, value = line.split(":", 1)
        meta[key.strip()] = parse_value(value)
    body = "\n".join(lines[end + 1 :]).lstrip("\n")
    return meta, body


def read_frontmatter(path: Path):
    meta, body = split_frontmatter(path.read_text(encoding="utf-8-sig"))
    meta["_path"] = path
    meta["_body"] = body
    return meta


def card_paths():
    if not CARDS.exists():
        return []
    return [p for p in sorted(CARDS.rglob("*.md")) if not p.name.startswith("_")]


def discover_cards():
    cards, errors = [], []
    for path in card_paths():
        try:
            cards.append(read_frontmatter(path))
        except Exception as exc:  # noqa: BLE001 - 汇总给用户看
            errors.append((path, str(exc)))
    return cards, errors


def set_meta_value(path: Path, key: str, value: str):
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0].strip() != "---":
        raise CardError("缺少 frontmatter")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        raise CardError("frontmatter 没有结束标记")
    for i in range(1, end):
        if lines[i].split(":", 1)[0].strip() == key:
            lines[i] = f"{key}: {value}"
            break
    else:
        lines.insert(end, f"{key}: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def core_point(card) -> str:
    match = re.search(r"【核心知识点】\s*([^\n]+)", card["_body"])
    if match:
        text = match.group(1).strip()
    else:
        candidates = [
            line.strip()
            for line in card["_body"].splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        text = candidates[0] if candidates else str(card.get("title") or "")
    text = re.sub(r"\s+", " ", text)
    return text if len(text) <= 100 else text[:97] + "..."


def format_card_link(card) -> str:
    rel = os.path.relpath(card["_path"].resolve(), TOPICS).replace("\\", "/")
    if " " in rel:
        rel = f"<{rel}>"
    return f"[{card.get('title') or card['id']}]({rel})"


def render_cards(cards) -> str:
    if not cards:
        return ""
    cards = sorted(cards, key=lambda c: str(c.get("created") or ""), reverse=True)
    lines = []
    for card in cards:
        lines.append(
            f"- **{card.get('created', '')}** {format_card_link(card)} — {core_point(card)}"
            f"（{card.get('type', '')} / {card.get('source', '')} / 置信度{card.get('confidence', '')}）"
        )
    return "\n".join(lines)


def replace_block(text: str, start: str, end: str, content: str) -> str:
    if start not in text or end not in text:
        raise CardError(f"缺少标记 {start} / {end}")
    pre, rest = text.split(start, 1)
    _, post = rest.split(end, 1)
    inner = "\n" + content.strip() + "\n" if content.strip() else "\n"
    return pre + start + inner + end + post


def ensure_block(text: str, heading: str, start: str, end: str) -> str:
    if start in text and end in text:
        return text
    block = f"\n\n{start}\n{end}\n\n"
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$", re.M)
    match = pattern.search(text)
    if not match:
        return text.rstrip() + f"\n\n## {heading}\n{block}"
    start_pos = match.end()
    next_heading = re.search(r"^## ", text[start_pos:], re.M)
    end_pos = start_pos + next_heading.start() if next_heading else len(text)
    return text[:start_pos] + block + text[end_pos:]


def topic_template(topic: str) -> str:
    return f"""---
topic: {topic}
description: （待补充：一句话说明这个主题解决什么问题）
tags: []
---

# {topic}

## 通用方法论

（尚未归纳。积累卡片后运行 `/consolidate {topic}` 生成。）

## 案例

（由 `/consolidate` 归纳；原始案例见下方卡片链接。）

## 知识卡片流水

{ACTIVE_START}
{ACTIVE_END}

## 历史卡片（已归纳）

{ARCHIVE_START}
{ARCHIVE_END}
"""


def read_topic_meta(path: Path):
    try:
        meta, _ = split_frontmatter(path.read_text(encoding="utf-8-sig"))
        return meta
    except Exception:  # noqa: BLE001 - 主题页 frontmatter 是可选的
        return {}


def build_index(cards) -> None:
    by_topic = {}
    for card in cards:
        by_topic.setdefault(str(card.get("topic") or "未分类"), []).append(card)

    rows = []
    for page in sorted(TOPICS.glob("*.md")):
        if page.name in ("INDEX.md", "README.md"):
            continue
        topic = page.stem
        meta = read_topic_meta(page)
        desc = str(meta.get("description") or "（待补充）").strip().replace("|", r"\|")
        topic_cards = by_topic.get(topic, [])
        active = [c for c in topic_cards if c.get("status") == "active"]
        dates = [str(c.get("created")) for c in topic_cards if c.get("created")]
        updated = (
            max(dates)
            if dates
            else datetime.fromtimestamp(page.stat().st_mtime).strftime("%Y-%m-%d")
        )
        rows.append((updated, topic, desc, len(active)))

    rows.sort(key=lambda row: (row[0], row[1]), reverse=True)
    lines = [
        "# 主题索引",
        "",
        "> 由 `python deploy/scripts/kb.py build` 自动生成，请勿手工编辑。",
        "> 新任务开始时先看这里，或直接运行 `/recall <关键词>`。",
        "",
        "| 主题 | 说明 | 活跃卡片 | 最近更新 |",
        "|---|---|---:|---|",
    ]
    for updated, topic, desc, count in rows:
        lines.append(f"| [{topic}]({topic}.md) | {desc} | {count} | {updated} |")
    if not rows:
        lines.append("| （暂无主题） | 运行 `/distill` 创建第一张卡片 | 0 | - |")
    lines.append("")
    INDEX.write_text("\n".join(lines), encoding="utf-8")
    print(f"[更新] {INDEX.relative_to(ROOT)}: {len(rows)} 个主题")


def build(topic_filter: Optional[str] = None) -> int:
    TOPICS.mkdir(parents=True, exist_ok=True)
    cards, errors = discover_cards()
    for path, error in errors:
        print(f"[错误] {path}: {error}", file=sys.stderr)

    by_topic = {}
    for card in cards:
        by_topic.setdefault(str(card.get("topic") or "未分类"), []).append(card)

    topics_to_build = [topic_filter] if topic_filter else sorted(by_topic)
    for topic in topics_to_build:
        page = TOPICS / f"{topic}.md"
        if not page.exists():
            page.write_text(topic_template(topic), encoding="utf-8")
            print(f"[新建] {page.relative_to(ROOT)}")
        text = page.read_text(encoding="utf-8-sig")
        text = ensure_block(text, "知识卡片流水", ACTIVE_START, ACTIVE_END)
        text = ensure_block(text, "历史卡片（已归纳）", ARCHIVE_START, ARCHIVE_END)
        topic_cards = by_topic.get(topic, [])
        active = [c for c in topic_cards if c.get("status") == "active"]
        archived = [c for c in topic_cards if c.get("status") in ("consolidated", "archived")]
        text = replace_block(text, ACTIVE_START, ACTIVE_END, render_cards(active))
        text = replace_block(text, ARCHIVE_START, ARCHIVE_END, render_cards(archived))
        page.write_text(text, encoding="utf-8")
        print(
            f"[更新] {page.relative_to(ROOT)}: active={len(active)}, archived={len(archived)}"
        )

    build_index(cards)
    return 1 if errors else 0


def recall(query: str, limit: int = 5, include_consolidated: bool = False) -> int:
    cards, errors = discover_cards()
    q = query.strip().lower()
    tokens = [token for token in re.split(r"[\s,，、/]+", q) if token]
    scored = []
    for card in cards:
        if card.get("status") != "active" and not include_consolidated:
            continue
        score = 0
        topic = str(card.get("topic") or "").lower()
        title = str(card.get("title") or "").lower()
        tags = [str(tag).lower() for tag in (card.get("tags") or [])]
        body = card["_body"].lower()
        if q == topic:
            score += 100
        elif q in topic or topic in q:
            score += 50
        for token in tokens:
            if token in topic:
                score += 40
            if token in title:
                score += 30
            if token in tags:
                score += 25
            score += min(body.count(token), 5) * 5
        try:
            created = datetime.strptime(str(card.get("created")), "%Y-%m-%d").date()
            score += max(0, 15 - (date.today() - created).days // 30)
        except Exception:  # noqa: BLE001 - 日期异常不影响检索
            pass
        score += {"高": 10, "中": 5, "低": 0}.get(card.get("confidence"), 0)
        if score > 0:
            scored.append((score, card))

    scored.sort(key=lambda item: (item[0], str(item[1].get("created") or "")), reverse=True)
    print(f"查询: {query}")
    print(f"索引: {INDEX.relative_to(ROOT)}")
    if errors:
        print(f"[警告] {len(errors)} 张卡片解析失败", file=sys.stderr)
    if not scored:
        print("未找到相关卡片。可以换一个关键词，或先用 /distill 积累卡片。")
        return 0

    print(f"命中 {min(limit, len(scored))} 张卡片:\n")
    for i, (_, card) in enumerate(scored[:limit], 1):
        rel = card["_path"].resolve().relative_to(ROOT).as_posix()
        print(f"[{i}] {card.get('created', '')} | {card.get('title', '')}")
        print(
            f"    主题: {card.get('topic', '')} | 类型: {card.get('type', '')} | "
            f"来源: {card.get('source', '')} | 置信度: {card.get('confidence', '')} | "
            f"状态: {card.get('status', '')}"
        )
        print(f"    核心: {core_point(card)}")
        print(f"    卡片: {rel}")
        print(f"    方法论: topics/{card.get('topic', '')}.md")
    return 0


def resolve_paths(items):
    paths = []
    for item in items:
        path = Path(item)
        if not path.is_absolute():
            candidate = ROOT / path
            if candidate.exists():
                path = candidate
        paths.append(path.resolve())
    return paths


def validate(paths) -> int:
    paths = resolve_paths(paths) if paths else card_paths()
    errors = []
    ids = {}
    for path in paths:
        try:
            card = read_frontmatter(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path}: {exc}")
            continue
        for key in REQUIRED:
            if key not in card or card[key] in (None, ""):
                errors.append(f"{path}: 缺少字段 {key}")
        for key, allowed in ALLOWED.items():
            if card.get(key) is not None and card.get(key) not in allowed:
                errors.append(f"{path}: {key}={card.get(key)!r} 不在 {sorted(allowed)} 中")
        for key in ("created", "review_after"):
            value = card.get(key)
            if value:
                try:
                    datetime.strptime(str(value), "%Y-%m-%d")
                except ValueError:
                    errors.append(f"{path}: {key} 不是 YYYY-MM-DD")
        topic = card.get("topic")
        if topic and path.parent.name != topic:
            errors.append(f"{path}: topic={topic!r} 与目录 {path.parent.name!r} 不一致")
        created = card.get("created")
        if created and not path.name.startswith(str(created)):
            errors.append(f"{path}: 文件名应以 created 日期 {created} 开头")
        card_id = card.get("id")
        if card_id:
            if card_id in ids:
                errors.append(f"{path}: id={card_id!r} 与 {ids[card_id]} 重复")
            else:
                ids[card_id] = path
        for marker in ("【核心知识点】", "【通用方法/原则】", "【适用条件】"):
            if marker not in card["_body"]:
                errors.append(f"{path}: 正文缺少 {marker}")

    if errors:
        print(f"校验失败（{len(errors)} 个问题）:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"校验通过：{len(paths)} 张卡片")
    return 0


def scan(paths) -> int:
    paths = resolve_paths(paths) if paths else card_paths()
    findings = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except Exception as exc:  # noqa: BLE001
            findings.append((path, 0, f"读取失败: {exc}"))
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for name, pattern in SECRET_PATTERNS:
                if re.search(pattern, line):
                    findings.append((path, lineno, name))
    if findings:
        print(f"发现 {len(findings)} 处可疑内容（请人工确认，不要直接提交）:")
        for path, lineno, name in findings:
            print(f"  - {path}:{lineno}: {name}")
        return 1
    print(f"扫描通过：{len(paths)} 个文件未发现常见密钥模式")
    return 0


def list_cards(topic: str, status: Optional[str] = None) -> int:
    cards, _ = discover_cards()
    rows = [
        card
        for card in cards
        if card.get("topic") == topic and (status is None or card.get("status") == status)
    ]
    if not rows:
        print(f"主题 {topic!r} 下没有符合条件的卡片。")
        return 0
    print(f"主题: {topic} | 状态: {status or '全部'} | 数量: {len(rows)}")
    for card in sorted(rows, key=lambda c: str(c.get("created") or ""), reverse=True):
        rel = card["_path"].resolve().relative_to(ROOT).as_posix()
        print(
            f"{card.get('id', '')}\t{card.get('status', '')}\t{card.get('created', '')}\t"
            f"{card.get('title', '')}\t{rel}"
        )
    return 0


def mark(topic: str, status: str, ids: Optional[str] = None) -> int:
    cards, _ = discover_cards()
    wanted = {item.strip() for item in ids.split(",") if item.strip()} if ids else None
    selected = []
    for card in cards:
        if card.get("topic") != topic:
            continue
        if wanted is not None and card.get("id") not in wanted:
            continue
        if wanted is None and card.get("status") != "active":
            continue
        selected.append(card)

    if not selected:
        print("没有需要标记的卡片。")
        return 1

    today = date.today().isoformat()
    for card in selected:
        set_meta_value(card["_path"], "status", status)
        if status == "consolidated":
            set_meta_value(card["_path"], "consolidated_at", today)
        print(f"[标记] {card['_path'].relative_to(ROOT).as_posix()} -> {status}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="个人知识库工具")
    sub = parser.add_subparsers(dest="command", required=True)

    p_build = sub.add_parser("build", help="重建主题页卡片区和主题索引")
    p_build.add_argument("--topic")

    p_recall = sub.add_parser("recall", help="检索卡片")
    p_recall.add_argument("query")
    p_recall.add_argument("--limit", type=int, default=5)
    p_recall.add_argument("--include-consolidated", action="store_true")

    p_validate = sub.add_parser("validate", help="校验卡片 schema")
    p_validate.add_argument("paths", nargs="*")

    p_scan = sub.add_parser("scan", help="扫描常见密钥模式")
    p_scan.add_argument("paths", nargs="*")

    p_list = sub.add_parser("list", help="列出某主题的卡片")
    p_list.add_argument("topic")
    p_list.add_argument("--status")

    p_mark = sub.add_parser("mark", help="批量更新卡片状态")
    p_mark.add_argument("topic")
    p_mark.add_argument("--status", required=True, choices=sorted(ALLOWED["status"]))
    p_mark.add_argument("--ids")

    args = parser.parse_args()

    if args.command == "build":
        return build(args.topic)
    if args.command == "recall":
        return recall(args.query, args.limit, args.include_consolidated)
    if args.command == "validate":
        return validate(args.paths)
    if args.command == "scan":
        return scan(args.paths)
    if args.command == "list":
        return list_cards(args.topic, args.status)
    if args.command == "mark":
        return mark(args.topic, args.status, args.ids)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
