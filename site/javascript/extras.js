(() => {
  const cloud = document.querySelector('.blogging-tags-grid');
  if (cloud) {
    const groups = new Map();
    const allPosts = new Map();
    const sourceNodes = [];
    document.querySelectorAll('.md-content h3[id]').forEach(heading => {
      const posts = [];
      sourceNodes.push(heading);
      for (let node = heading.nextElementSibling; node && node.tagName !== 'H3'; node = node.nextElementSibling) {
        if (node.tagName !== 'LI' && node.tagName !== 'UL') continue;
        sourceNodes.push(node);
        const items = node.tagName === 'LI' ? [node] : node.querySelectorAll('li');
        items.forEach(item => {
          const link = item.querySelector('a');
          if (!link) return;
          const url = new URL(link.href);
          const post = { title: link.textContent.trim(), href: url.pathname + url.search + url.hash,
            date: item.querySelector('span')?.textContent.trim() || '' };
          posts.push(post);
          allPosts.set(post.href, post);
        });
      }
      groups.set(heading.id, posts);
    });
    const links = Array.from(cloud.querySelectorAll('.blogging-tag'));
    const tagName = link => decodeURIComponent(link.hash.slice(1));
    links.sort((a, b) => (groups.get(tagName(b))?.length || 0) - (groups.get(tagName(a))?.length || 0));
    links.forEach(link => {
      const name = tagName(link);
      const count = groups.get(name)?.length || 0;
      const level = count >= 5 ? 3 : count >= 3 ? 2 : count >= 2 ? 1 : 0;
      link.href = `#${encodeURIComponent(name)}`;
      link.style.setProperty('--tag-weight', String(level));
      link.dataset.level = String(level);
      link.textContent = name;
      const badge = document.createElement('span');
      badge.className = 'tag-count';
      badge.textContent = count;
      badge.setAttribute('aria-hidden', 'true');
      link.append(badge);
      link.title = `${name} · ${count} 篇文章`;
      link.setAttribute('aria-label', link.title);
      cloud.append(link);
    });
    const results = document.createElement('section');
    results.className = 'tag-results';
    results.setAttribute('aria-labelledby', 'tag-results-title');
    const header = document.createElement('div');
    header.className = 'tag-results__header';
    const title = document.createElement('h2');
    title.id = 'tag-results-title';
    title.className = 'tag-results__title';
    title.setAttribute('aria-live', 'polite');
    title.setAttribute('aria-atomic', 'true');
    const reset = document.createElement('button');
    reset.type = 'button';
    reset.className = 'tag-results__reset';
    reset.textContent = '查看全部';
    const list = document.createElement('ul');
    list.className = 'tag-results__list';
    header.append(title, reset);
    results.append(header, list);
    cloud.after(results);
    // Keep the generated index readable when JavaScript is unavailable.
    sourceNodes.forEach(node => { node.hidden = true; node.removeAttribute('id'); });
    const render = () => {
      let selected;
      try { selected = decodeURIComponent(location.hash.slice(1)); } catch (_) { selected = ''; }
      const active = groups.has(selected);
      const posts = active ? groups.get(selected) : Array.from(allPosts.values());
      title.textContent = `${active ? selected : '全部文章'} · ${posts.length} 篇`;
      reset.hidden = !active;
      links.forEach(link => {
        if (active && tagName(link) === selected) link.setAttribute('aria-current', 'true');
        else link.removeAttribute('aria-current');
      });
      list.replaceChildren();
      [...posts].sort((a, b) => b.date.localeCompare(a.date)).forEach(post => {
        const item = document.createElement('li');
        const link = document.createElement('a');
        link.href = post.href;
        link.textContent = post.title;
        const date = document.createElement('time');
        date.dateTime = post.date;
        date.textContent = post.date;
        item.append(link, date);
        list.append(item);
      });
    };
    cloud.addEventListener('click', event => {
      const link = event.target.closest('.blogging-tag');
      if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0) return;
      event.preventDefault();
      history.pushState(null, '', link.hash);
      render();
    });
    reset.addEventListener('click', () => {
      history.pushState(null, '', location.pathname + location.search);
      render();
      links[0]?.focus({ preventScroll: true });
    });
    addEventListener('hashchange', render);
    addEventListener('popstate', render);
    render();
  }

  const article = /^\/blog\/\d{4}\/[^/]+\/?$/.test(location.pathname);
  if (article) {
    const bar = document.createElement('div');
    bar.className = 'reading-progress';
    bar.setAttribute('aria-hidden', 'true');
    document.body.appendChild(bar);
    const update = () => {
      const available = document.documentElement.scrollHeight - innerHeight;
      bar.style.transform = `scaleX(${available > 0 ? Math.min(1, scrollY / available) : 1})`;
    };
    addEventListener('scroll', update, { passive: true });
    addEventListener('resize', update, { passive: true });
    update();
  }

  document.addEventListener('click', async event => {
    const button = event.target.closest('.random-post');
    if (!button) return;
    button.disabled = true;
    const original = button.textContent;
    button.textContent = '寻找文章…';
    try {
      const indexUrl = new URL(button.dataset.index, location.href);
      const response = await fetch(indexUrl);
      if (!response.ok) throw new Error('Search index unavailable');
      const index = await response.json();
      const posts = index.docs.filter(item => /^blog\/\d{4}\/[^/]+\/$/.test(item.location));
      if (!posts.length) throw new Error('No posts found');
      const chosen = posts[Math.floor(Math.random() * posts.length)];
      location.href = new URL(chosen.location, new URL('../', indexUrl)).href;
    } catch (_) {
      button.textContent = '暂时无法抽取';
      setTimeout(() => { button.textContent = original; button.disabled = false; }, 2000);
    }
  });
})();
