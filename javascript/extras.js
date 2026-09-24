(() => {
  const cloud = document.querySelector('.blogging-tags-grid');
  if (cloud) {
    const counts = new Map();
    document.querySelectorAll('.md-content h3[id]').forEach(heading => {
      let count = 0;
      for (let node = heading.nextElementSibling; node && node.tagName !== 'H3'; node = node.nextElementSibling) {
        if (node.tagName === 'LI') {
          count += 1;
          node.classList.add('tag-article-item');
        } else {
          count += node.querySelectorAll('li').length;
        }
      }
      counts.set(heading.id, count);
    });
    cloud.querySelectorAll('.blogging-tag').forEach(link => {
      const name = decodeURIComponent(link.hash.slice(1));
      const count = counts.get(name) || 1;
      link.href = `#${encodeURIComponent(name)}`;
      link.style.setProperty('--tag-weight', String(Math.min(4, Math.log2(count))));
      link.title = `${name} · ${count} 篇文章`;
      link.setAttribute('aria-label', link.title);
    });
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
