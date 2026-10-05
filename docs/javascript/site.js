(() => {
  const uptime = document.getElementById('site-uptime');
  if (!uptime) return;

  const startedAt = Date.parse(uptime.dateTime);
  if (!Number.isFinite(startedAt)) return;

  function updateUptime() {
    const elapsedSeconds = Math.max(0, Math.floor((Date.now() - startedAt) / 1000));
    const days = Math.floor(elapsedSeconds / 86400);
    const hours = Math.floor((elapsedSeconds % 86400) / 3600);
    const minutes = Math.floor((elapsedSeconds % 3600) / 60);
    const seconds = elapsedSeconds % 60;
    uptime.textContent = `${days} 天 ${hours} 小时 ${minutes} 分钟 ${seconds} 秒`;
  }

  updateUptime();
  window.setInterval(updateUptime, 1000);
})();


(() => {
  const button = document.querySelector('.friend-copy');
  if (!button) return;
  const tools = document.querySelector('.friend-copy-tools');
  const status = document.querySelector('.friend-copy-status');
  const fallback = document.querySelector('.friend-copy-fallback');
  tools.hidden = false;
  button.addEventListener('click', async () => {
    const text = Array.from(document.querySelectorAll('.friend-info__row'))
      .map(row => `${row.querySelector('.friend-info__label').textContent.trim()}：${row.querySelector('.friend-info__value').textContent.trim()}`)
      .join('\n');
    try {
      await navigator.clipboard.writeText(text);
      status.textContent = '已复制，可以粘贴到对方的留言区。';
      fallback.hidden = true;
    } catch (_) {
      fallback.value = text;
      fallback.hidden = false;
      fallback.focus();
      fallback.select();
      status.textContent = '请复制下方已选中的信息。';
    }
  });
})();
