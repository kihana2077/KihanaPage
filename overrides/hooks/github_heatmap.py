"""Render the GitHub contribution calendar of a user as an inline SVG.

The markdown source only contains ``{{ github_heatmap }}``; this hook replaces
that placeholder with an SVG rendered from GitHub's public contribution page, so
the markdown stays readable and the data does not depend on a third-party image
service at page load.

If GitHub cannot be reached (offline build, rate limiting), the placeholder is
replaced with a short notice and a link to the profile instead of failing the
build.
"""

from __future__ import annotations

import datetime as dt
import functools
import html
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

PLACEHOLDER = "{{ github_heatmap }}"
CACHE_PATH = Path(__file__).resolve().parent / ".__gh_heatmap_cache__" / "contributions.json"
CACHE_TTL = dt.timedelta(days=30)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"
)

USERNAME = "kihana2077"
REPO_RE = re.compile(r"github\.com/(?P<user>[\w.-]+)/", re.IGNORECASE)
PROFILE_URL = f"https://github.com/{USERNAME}"

# GitHub colours the calendar green; this site uses a soft blue palette, so the
# rendered SVG points at CSS custom properties instead of fixed colours.
LEVEL_CLASS = {
    0: "gh-heatmap__day--l0",
    1: "gh-heatmap__day--l1",
    2: "gh-heatmap__day--l2",
    3: "gh-heatmap__day--l3",
    4: "gh-heatmap__day--l4",
}
CELL = 12.8
GAP = 4.1
PITCH = CELL + GAP
ROWS = 7
LEFT = 32.0
TOP = 18.0
RADIUS = 2.5
# Trailing space after the last column. The graph's own right edge is placed at
# the viewBox edge minus this, so the grid runs to the card edge instead of
# stopping short; the same amount covers the last month label's overhang.
RIGHT = 26.0
LABEL_FONT = 8
MONTH_BASELINE = 10.0
WEEKDAY_BASELINE = CELL / 2 + 3.6
# Measured width of one 8px glyph in user units when the SVG renders at its
# natural size (about 4.7 units for the site's font stack); a three letter month
# name is roughly 15 units wide. Wide enough to keep short months honest, small
# enough that every month of a 53 column year still gets a label.
LABEL_CHAR = 5.6
MONTHS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)

_DAY_CELL_RE = re.compile(r"<td\b(?P<attrs>[^>]*)>", re.IGNORECASE)
_DATE_ATTR_RE = re.compile(r'data-date="(?P<date>\d{4}-\d{2}-\d{2})"')
_LEVEL_ATTR_RE = re.compile(r'data-level="(?P<level>\d)"')
_TIP_RE = re.compile(r"<tool-tip[^>]*>(?P<text>.*?)</tool-tip>", re.DOTALL)
_TOTAL_RE = re.compile(r"([\d,]+)\s*contributions?\s+in the last year")


def _pretty(date: str) -> str:
    """Fallback label that does not rely on platform specific strftime codes."""
    try:
        day = dt.date.fromisoformat(date)
    except ValueError:
        return date
    return f"{MONTHS[day.month - 1]} {day.day}, {day.year}"


def _fetch(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def _parse(page: str) -> dict:
    """Turn the contribution page into days, tooltip labels and a total.

    Attributes are read per ``<td>`` rather than with one combined pattern: the
    attribute order inside a day cell is not guaranteed, and an order-sensitive
    regex silently returned the days shuffled, which scrambled the whole grid.
    """
    days: list[tuple[str, int]] = []
    for match in _DAY_CELL_RE.finditer(page):
        attrs = match.group("attrs")
        date = _DATE_ATTR_RE.search(attrs)
        level = _LEVEL_ATTR_RE.search(attrs)
        if date and level:
            days.append((date.group("date"), int(level.group("level"))))
    if not days:
        raise ValueError("no contribution days found in the fetched page")

    tips = [
        html.unescape(re.sub(r"\s+", " ", match.group("text"))).strip()
        for match in _TIP_RE.finditer(page)
    ]
    # Pair by position only when the day cells really are in calendar order;
    # sorting first keeps the grid correct even if the markup is reordered.
    ordered = sorted(days, key=lambda item: item[0])
    if ordered != days:
        tips = []
    labels = [
        tips[index] if index < len(tips) else _pretty(date)
        for index, (date, _level) in enumerate(ordered)
    ]

    total = _TOTAL_RE.search(page)
    return {
        "days": ordered,
        "labels": labels,
        "total": total.group(1) if total else None,
    }


def _load(username: str) -> dict:
    """Fetch the calendar, falling back to a recent cache when offline.

    The bare URL renders the full calendar; adding ``?from=&to=`` makes GitHub
    return a reduced page without the day labels and the yearly total, so the
    plain endpoint is the one worth parsing.
    """
    url = f"https://github.com/users/{username}/contributions"
    try:
        data = _parse(_fetch(url))
        data["username"] = username
        data["fetched"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        try:
            CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            CACHE_PATH.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
        return data
    except (urllib.error.URLError, TimeoutError, ValueError, OSError, UnicodeError):
        pass

    try:
        cached = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        if cached.get("username") != username:
            raise ValueError("cache belongs to another user")
        fetched = dt.datetime.fromisoformat(cached["fetched"])
        if dt.datetime.now(dt.timezone.utc) - fetched > CACHE_TTL:
            raise ValueError("cache is stale")
        cached["from_cache"] = True
        return cached
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return {"days": [], "labels": [], "total": None, "username": username}


def _month_labels(days: list[tuple[str, int]]) -> list[tuple[float, str]]:
    """Return ``(x, name)`` for the first week of each month, dropping collisions.

    ``x`` is the absolute user-unit coordinate: the caller writes it straight
    into the SVG, so ``LEFT`` is applied here exactly once.
    """
    labels: list[tuple[float, str]] = []
    seen: set[str] = set()
    last_end = float("-inf")
    for index, (date, _level) in enumerate(days):
        day = dt.date.fromisoformat(date)
        key = f"{day.year}-{day.month}"
        if key in seen:
            continue
        seen.add(key)
        x = LEFT + (index // ROWS) * PITCH
        # Width is per character, not per label: a three letter month often fits
        # where a long one does not.
        width = len(MONTHS[day.month - 1]) * LABEL_CHAR
        if x < last_end:
            continue
        labels.append((x, MONTHS[day.month - 1]))
        last_end = x + width
    return labels


def _profile_url(config: dict | None) -> str:
    """Prefer the account from ``repo_url`` so the hook follows the site config."""
    repo = str((config or {}).get("repo_url") or "")
    found = REPO_RE.search(repo)
    return f"https://github.com/{found.group('user')}" if found else PROFILE_URL


def _render(data: dict) -> str:
    profile = data.get("profile_url") or PROFILE_URL
    days = data["days"]
    if not days:
        return (
            '<p class="gh-heatmap__fallback">暂时取不到 GitHub 贡献数据，'
            f'可以到 <a href="{profile}" target="_blank" rel="noopener">GitHub 主页</a>查看。</p>'
        )

    columns = (len(days) + ROWS - 1) // ROWS
    # The grid's own right edge lands just inside the viewBox, so it lines up
    # with the card instead of stopping short, and the last month label has a
    # little room to overhang the final column.
    width = LEFT + columns * PITCH + RIGHT
    height = TOP + ROWS * PITCH

    parts = [
        f'<svg class="gh-heatmap__svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}" role="img" '
        'aria-label="GitHub 贡献热力图">',
    ]
    # Font sizes are set as presentation attributes: the site stylesheet already
    # styles these classes, but an attribute cannot be lost to a more specific
    # rule from the theme, which is what made the month labels overlap.

    for x, label in _month_labels(days):
        # x is already absolute; a label must not run past the viewBox.
        if x + len(label) * LABEL_CHAR > width:
            continue
        parts.append(
            f'<text class="gh-heatmap__month" x="{x:.1f}" '
            f'y="{MONTH_BASELINE:.1f}" font-size="{LABEL_FONT}">{label}</text>'
        )

    for row, name in enumerate(("Mon", "Wed", "Fri")):
        y = TOP + (row * 2 + 1) * PITCH + WEEKDAY_BASELINE
        parts.append(
            f'<text class="gh-heatmap__weekday" x="0" y="{y:.1f}" '
            f'font-size="{LABEL_FONT}">{name}</text>'
        )

    for index, (date, level) in enumerate(days):
        column, row = divmod(index, ROWS)
        x = LEFT + column * PITCH
        y = TOP + row * PITCH
        label = html.escape(data["labels"][index] or date, quote=True)
        parts.append(
            f'<rect class="gh-heatmap__day {LEVEL_CLASS.get(level, LEVEL_CLASS[0])}" '
            f'x="{x:.1f}" y="{y:.1f}" width="{CELL:.0f}" height="{CELL:.0f}" '
            f'rx="{RADIUS:.1f}" data-date="{date}" data-level="{level}">'
            f"<title>{label}</title></rect>"
        )

    parts.append("</svg>")

    total = data.get("total")
    count = f"{total} 次贡献" if total else f"{len(days)} 天"
    note = f"（缓存于 {html.escape(data["fetched"][:10])}）" if data.get("from_cache") else ""
    return (
        '<figure class="gh-heatmap">'
        f'<div class="gh-heatmap__head"><strong>{count}</strong>'
        f'<span>过去一年 · @{html.escape(data["username"])}{note}</span></div>'
        '<div class="gh-heatmap__scroll" tabindex="0" role="region" aria-label="GitHub 贡献日历，可横向滚动">'
        + "".join(parts)
        + "</div>"
        '<div class="gh-heatmap__legend"><span>少</span>'
        + "".join(
            f'<i class="gh-heatmap__day {LEVEL_CLASS[level]}"></i>' for level in range(5)
        )
        + "<span>多</span>"
        f'<a href="{profile}" target="_blank" rel="noopener">GitHub 主页 ↗</a>'
        "</div></figure>"
    )


@functools.lru_cache(maxsize=4)
def _svg(username: str, profile: str) -> str:
    data = _load(username)
    data["profile_url"] = profile
    return _render(data)


def on_page_markdown(markdown: str, config=None, **kwargs) -> str:
    if PLACEHOLDER not in markdown:
        return markdown
    return markdown.replace(PLACEHOLDER, _svg(USERNAME, _profile_url(config)))
