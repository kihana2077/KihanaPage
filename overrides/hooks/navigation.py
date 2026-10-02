"""Keep the automatically discovered article tree while ordering the main tabs."""


ORDER = {
    "index.md": 0,
    "blog/index.md": 1,
    "tags.md": 2,
    "toc.md": 3,
    "friend.md": 4,
    "contact.md": 5,
}


def on_nav(nav, config, files):
    for item in nav.items:
        if item.is_section and item.title == "Blog":
            item.title = "文章"

    def rank(item):
        if item.is_page:
            return ORDER.get(item.file.src_uri, len(ORDER))
        if item.is_section and item.title == "文章":
            return ORDER["blog/index.md"]
        return len(ORDER)

    nav.items.sort(key=rank)

    # Keep MkDocs' previous/next links in the same order as the visible tabs.
    pages = []

    def collect(items):
        for item in items:
            if item.is_page:
                pages.append(item)
            elif item.is_section:
                collect(item.children)

    collect(nav.items)
    nav.pages[:] = pages
    for index, page in enumerate(pages):
        page.previous_page = pages[index - 1] if index else None
        page.next_page = pages[index + 1] if index + 1 < len(pages) else None
    return nav
