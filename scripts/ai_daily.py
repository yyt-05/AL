"""Collect public AI feeds without third-party packages or API credentials."""

import html
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "ai-daily"
FEEDS = [
    ("Hugging Face · 开源模型与实践", "https://huggingface.co/blog/feed.xml"),
    ("Google Research · 研究与方法", "https://research.google/blog/rss/"),
    ("arXiv cs.AI · AI 论文", "https://rss.arxiv.org/rss/cs.AI"),
]
ATOM = {"a": "http://www.w3.org/2005/Atom"}
UTC = timezone.utc


def clean(value):
    value = re.sub(r"<[^>]+>", " ", html.unescape(value or ""))
    return re.sub(r"\s+", " ", value).strip()


def published(value):
    try:
        date = parsedate_to_datetime(value)
    except (ValueError, TypeError):
        try:
            date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    return date.replace(tzinfo=UTC) if date.tzinfo is None else date.astimezone(UTC)


def parse_feed(data):
    root = ET.fromstring(data)
    entries = []
    for item in root.findall(".//item"):
        entries.append({
            "title": clean(item.findtext("title")),
            "url": (item.findtext("link") or "").strip(),
            "summary": clean(item.findtext("description")),
            "date": published(item.findtext("pubDate") or ""),
        })
    for item in root.findall("a:entry", ATOM):
        link = next((node.get("href", "") for node in item.findall("a:link", ATOM)
                     if node.get("rel", "alternate") == "alternate"), "")
        entries.append({
            "title": clean(item.findtext("a:title", "", ATOM)),
            "url": link,
            "summary": clean(item.findtext("a:summary", "", ATOM)
                             or item.findtext("a:content", "", ATOM)),
            "date": published(item.findtext("a:published", "", ATOM)
                              or item.findtext("a:updated", "", ATOM)),
        })
    return entries


def fetch(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "AL-AI-Daily/1.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                return parse_feed(response.read(5_000_000))
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def main():
    now = datetime.now(UTC)
    day = now.astimezone(timezone(timedelta(hours=8))).date().isoformat()
    report = ROOT / f"{day}.md"
    if report.exists():
        print("Today's report already exists; skipping duplicate run.")
        return
    state_path = ROOT / "seen.json"
    seen = set(json.loads(state_path.read_text(encoding="utf-8"))) if state_path.exists() else set()
    sections, failures, new_urls = [], [], set()
    successes = 0
    for name, url in FEEDS:
        try:
            items = fetch(url)
            if not items:
                raise ValueError("订阅源没有可解析条目")
            successes += 1
        except Exception as error:
            failures.append(name)
            print(f"Source failed: {name}: {error}", file=sys.stderr)
            continue
        selected = []
        for item in sorted(items, key=lambda entry: entry["date"] or datetime.min.replace(tzinfo=UTC), reverse=True):
            if not item["title"] or not item["url"].startswith(("https://", "http://")):
                continue
            if item["date"] is None or not now - timedelta(days=7) <= item["date"] <= now:
                continue
            if item["url"] in seen or item["url"] in new_urls:
                continue
            selected.append(item)
            new_urls.add(item["url"])
            if len(selected) == 3:
                break
        if selected:
            lines = [f"## {name}", ""]
            for item in selected:
                title = item["title"].replace("[", "（").replace("]", "）")
                lines += [f"### {title}", "", f"- 原文：<{item['url']}>",
                          f"- 发布日期：{item['date'].date().isoformat()}", "",
                          "来源摘要（保留原文）：", "",
                          "> " + (item["summary"][:600] or "来源未提供摘要，请阅读原文。"), ""]
            sections.append("\n".join(lines))
    if successes == 0:
        raise RuntimeError("所有来源获取失败，不写入日报或去重记录")
    ROOT.mkdir(parents=True, exist_ok=True)
    content = f"# AI 知识日报 · {day}\n\n"
    content += "> 从公开订阅源收集近 7 天未收录内容，每个来源最多 3 条；不代表全网覆盖。摘要为来源原文，未经过模型翻译或事实核验。\n\n"
    content += "\n".join(sections) or "今日没有符合时间范围的新条目。\n"
    content += "\n## 阅读建议\n\n选择一篇原文，记录它解决的问题、核心方法和适用限制；论文中的实验结果以原文为准。\n"
    if failures:
        content += "\n本次未能读取的来源：" + "、".join(failures) + "。\n"
    report.write_text(content, encoding="utf-8")
    state_path.write_text(json.dumps(sorted(seen | new_urls), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    reports = sorted(ROOT.glob("????-??-??.md"), reverse=True)
    index = "# 每日 AI 知识\n\n每天北京时间 09:15 自动收集，支持在 Actions 中手动运行。\n\n"
    index += "\n".join(f"- [{path.stem}]({path.name})" for path in reports) + "\n"
    (ROOT / "README.md").write_text(index, encoding="utf-8")
    print(f"Saved {report.name}: {len(new_urls)} new entries; {successes}/{len(FEEDS)} sources available.")


if __name__ == "__main__":
    main()
