"""Generate a small RSS feed for blog posts without another runtime dependency."""

from datetime import date, datetime, time
from email.utils import format_datetime
from pathlib import Path
import subprocess
from urllib.parse import urljoin
from xml.etree import ElementTree as ET
import re
from zoneinfo import ZoneInfo

import yaml


_posts = []


def on_pre_build(config):
    _posts.clear()


def on_page_markdown(markdown, page, config, files):
    if page.file.src_uri == "toc.md":
        markdown = markdown.replace("{{ chronological_index }}", _archive_markdown(config.docs_dir))
    # The blogging plugin reads a flat `time` value. Reuse the article's
    # existing `date.created` so the archive, tags and feed share one date.
    value = page.meta.get("date")
    if isinstance(value, dict) and value.get("created"):
        page.meta["time"] = value["created"]
    return markdown


def _archive_markdown(docs_dir):
    posts = []
    docs = Path(docs_dir)
    for source in (docs / "blog").glob("[0-9][0-9][0-9][0-9]/*.md"):
        if source.stem == "index":
            continue
        content = source.read_text(encoding="utf-8")
        meta = {}
        match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", content, re.S)
        if match:
            meta = yaml.safe_load(match.group(1)) or {}
        heading = re.search(r"^#\s+(.+)$", content, re.M)
        title = meta.get("title") or (heading.group(1).strip() if heading else source.stem)
        created = _created(meta.get("date"), source)
        posts.append((created, title, source.relative_to(docs).as_posix()))
    posts.sort(key=lambda item: item[0], reverse=True)
    lines = []
    current_year = None
    for created, title, source in posts:
        if created.year != current_year:
            current_year = created.year
            lines.extend(["", f"## {current_year}", ""])
        lines.append(f"- **{created:%Y-%m-%d}** [{title}]({source})")
    return "\n".join(lines)


def _created(value, source):
    if isinstance(value, dict):
        value = value.get("created")
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    if isinstance(value, date):
        return datetime.combine(value, time.min, ZoneInfo("Asia/Shanghai"))
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
        except ValueError:
            pass
    result = subprocess.run(
        ["git", "log", "--follow", "--diff-filter=A", "--format=%aI", "--", str(source)],
        capture_output=True, text=True, check=False,
    )
    first = result.stdout.strip().splitlines()
    return datetime.fromisoformat(first[-1]) if first else datetime.now().astimezone()


def on_page_context(context, page, config, nav):
    source = page.file.src_uri
    if not source.startswith("blog/") or not source.endswith(".md") or source.endswith("index.md"):
        return
    created = _created(page.meta.get("date"), Path(config.docs_dir) / source)
    _posts.append({
        "title": page.title,
        "url": urljoin(config.site_url, page.url),
        "created": created,
        "description": page.meta.get("description") or page.title,
        "tags": page.meta.get("tags", []),
    })


def on_post_build(config):
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    for tag, value in (
        ("title", config.site_name),
        ("link", config.site_url),
        ("description", config.site_description),
        ("language", "zh-CN"),
    ):
        ET.SubElement(channel, tag).text = value
    for post in sorted(_posts, key=lambda item: item["created"], reverse=True)[:30]:
        item = ET.SubElement(channel, "item")
        for tag, value in (
            ("title", post["title"]),
            ("link", post["url"]),
            ("guid", post["url"]),
            ("description", post["description"]),
            ("pubDate", format_datetime(post["created"])),
        ):
            ET.SubElement(item, tag).text = str(value)
        for category in post["tags"]:
            ET.SubElement(item, "category").text = str(category)
    destination = Path(config.site_dir) / "feed.xml"
    ET.ElementTree(root).write(destination, encoding="utf-8", xml_declaration=True)
