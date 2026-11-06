/* YunJing WebGL shell. All browser capabilities are optional and fail softly. */
(() => {
  'use strict';
  const q = id => document.getElementById(id);
  const shell = q('yj-shell'), canvas = q('unity-canvas');
  const enter = q('yj-enter'), progress = q('yj-progress'), ink = q('yj-ink');
  const progressText = q('yj-progress-text'), progressSize = q('yj-progress-size');
  const install = q('yj-install'), installAction = q('yj-install-action');
  const resume = q('yj-resume');
  let ready = false, entered = false, menuOpen = false, deferredInstall = null;
  const touch = matchMedia('(pointer: coarse)').matches;
  const query = new URLSearchParams(location.search);
  const preview = query.has('yj-preview');
  let dataBytes = 0;

  const setProgress = value => {
    const p = Math.max(0, Math.min(1, Number(value) || 0));
    ink.style.strokeDashoffset = String(100 * (1 - p));
    progressText.textContent = `${p >= 1 ? '入境' : p >= .9 ? '築基中…' : '凝氣中…'} ${Math.round(p * 100)}%`;
    progressSize.textContent = dataBytes ? `${(p * dataBytes / 1048576).toFixed(1)} / ${(dataBytes / 1048576).toFixed(1)} MB` : '';
  };
  const error = (message, kind) => {
    const raw = String(message || '未知錯誤');
    const lower = raw.toLowerCase();
    q('yj-error-text').textContent = kind === 'webgl' ? '此瀏覽器無法開啟承天。請改用最新版 Chrome、Edge 或 Safari。' : kind === 'memory' || lower.includes('memory') ? '裝置記憶體不足。請關閉其他分頁後重新整理。' : '入境失敗，可能是網路中斷。請檢查連線後重新整理。';
    q('yj-error-detail').textContent = raw;
    q('yj-error').hidden = false;
    progress.hidden = true; enter.hidden = true;
  };
  const isInstalled = () => query.has('installed') || matchMedia('(display-mode: standalone)').matches || matchMedia('(display-mode: fullscreen)').matches || navigator.standalone === true;
  const dismissed = () => { try { return localStorage.getItem('yj-install-dismissed') === '1'; } catch { return false; } };
  const showInstall = () => {
    if (isInstalled() || dismissed()) return;
    if (deferredInstall) { q('yj-install-text').textContent = '將承天加入主畫面'; installAction.hidden = false; install.hidden = false; }
    else if (/iPad|iPhone|iPod/.test(navigator.userAgent)) { q('yj-install-text').textContent = '點分享 → 加入主畫面，即可全螢幕遊玩'; installAction.hidden = true; install.hidden = false; }
    else if (preview && query.has('install')) { q('yj-install-text').textContent = '將承天加入主畫面'; installAction.hidden = false; install.hidden = false; }
  };
  const loaded = () => { ready = true; setProgress(1); progress.hidden = true; enter.hidden = false; showInstall(); };
  const start = () => {
    if (!ready || entered) return;
    entered = true;
    document.documentElement.requestFullscreen?.().catch(() => {});
    if (touch) screen.orientation?.lock?.('landscape')?.catch(() => {});
    else canvas.requestPointerLock?.();
    shell.classList.add('yj-vanish');
    canvas.focus();
  };
  enter.addEventListener('click', start);
  document.addEventListener('keydown', ev => { if (ready && !entered && ev.key !== 'Tab' && q('yj-error').hidden) start(); });
  q('yj-reload').addEventListener('click', () => location.reload());
  q('yj-install-close').addEventListener('click', () => { install.hidden = true; try { localStorage.setItem('yj-install-dismissed', '1'); } catch {} });
  installAction.addEventListener('click', async () => { try { deferredInstall?.prompt(); await deferredInstall?.userChoice; } catch {} install.hidden = true; deferredInstall = null; });
  window.addEventListener('beforeinstallprompt', ev => { ev.preventDefault(); deferredInstall = ev; if (ready) showInstall(); });
  resume.addEventListener('click', () => canvas.requestPointerLock?.());
  document.addEventListener('pointerlockchange', () => { resume.hidden = !entered || menuOpen || touch || document.pointerLockElement === canvas; });
  window.yjShell = { setMenuOpen(value) { menuOpen = Boolean(value); resume.hidden = menuOpen || document.pointerLockElement === canvas || !entered; }, error, setProgress, loaded };

  if (!preview && 'serviceWorker' in navigator) navigator.serviceWorker.register('ServiceWorker.js').catch(() => {});
  if (query.get('error') === 'webgl') { error('WebGL2 disabled for preview', 'webgl'); return; }
  if (!preview && !document.createElement('canvas').getContext('webgl2')) { error('WebGL2 unavailable', 'webgl'); return; }
  if (query.get('error') === 'memory') { error('Out of memory', 'memory'); return; }
  if (query.get('error') === 'load') { error('Mock network interruption', 'load'); return; }
  if (preview) {
    const duration = query.has('slow') ? 30000 : 8000;
    const began = performance.now();
    const timer = setInterval(() => { const p = Math.min(1, (performance.now() - began) / duration); setProgress(p); if (p >= 1) { clearInterval(timer); loaded(); } }, 80);
    return;
  }
  const { loaderUrl, config } = window.yjBuild;
  // HEAD can fail under restrictive hosting. A missing length only hides the MB line.
  fetch(config.dataUrl, { method: 'HEAD' }).then(r => { dataBytes = Number(r.headers.get('content-length')) || 0; }).catch(() => {});
  const loader = document.createElement('script'); loader.src = loaderUrl;
  loader.onload = () => window.createUnityInstance(canvas, config, setProgress).then(loaded).catch(error);
  loader.onerror = () => error('Unity loader download failed', 'load');
  document.body.appendChild(loader);
})();
