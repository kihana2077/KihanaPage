// Optional, lightweight snow. The reader can switch it off at any time.
(() => {
  const storageKey = 'kihana-snow';
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const canvas = document.createElement('canvas');
  canvas.id = 'snow-canvas';
  canvas.setAttribute('aria-hidden', 'true');
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  let flakes = [];
  let frame = 0;
  let last = 0;
  let enabled = localStorage.getItem(storageKey) === 'on' && !motion.matches;

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    flakes = Array.from({ length: Math.min(48, Math.ceil(canvas.width / 28)) }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      r: 1 + Math.random() * 2,
      speed: 0.3 + Math.random() * 0.8
    }));
  }

  function paint(time) {
    if (!enabled) return;
    frame = requestAnimationFrame(paint);
    if (time - last < 50) return;
    last = time;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = 'rgba(220, 235, 255, 0.75)';
    for (const flake of flakes) {
      flake.y += flake.speed;
      flake.x += Math.sin(flake.y / 45) * 0.25;
      if (flake.y > canvas.height + 3) flake.y = -3;
      if (flake.x > canvas.width + 3) flake.x = -3;
      ctx.beginPath();
      ctx.arc(flake.x, flake.y, flake.r, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  function syncButtons() {
    document.querySelectorAll('.snow-toggle').forEach(button => {
      button.textContent = `✨ 动态${enabled ? '开' : '关'}`;
      button.setAttribute('aria-pressed', String(enabled));
      button.setAttribute('aria-label', `${enabled ? '关闭' : '开启'}页面动态效果`);
    });
  }

  function setEnabled(value) {
    enabled = value && !motion.matches;
    localStorage.setItem(storageKey, enabled ? 'on' : 'off');
    canvas.hidden = !enabled;
    cancelAnimationFrame(frame);
    if (enabled) frame = requestAnimationFrame(paint);
    else ctx.clearRect(0, 0, canvas.width, canvas.height);
    syncButtons();
  }

  document.body.appendChild(canvas);
  resize();
  window.addEventListener('resize', resize, { passive: true });
  motion.addEventListener('change', () => setEnabled(enabled));
  document.addEventListener('click', event => {
    if (event.target.closest('.snow-toggle')) setEnabled(!enabled);
  });
  setEnabled(enabled);
})();
