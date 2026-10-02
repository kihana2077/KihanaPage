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
