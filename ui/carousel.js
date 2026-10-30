/* Six7 real-app gallery. No autoplay, global arrow shortcuts, or synthetic UI. */
(() => {
  'use strict';
  const root = document.getElementById('apps');
  const source = document.getElementById('app-data');
  if (!root || !source) return;
  const data = JSON.parse(source.textContent);
  const tabs = [...root.querySelectorAll('.product-tab')];
  const panels = [...root.querySelectorAll('.product-panel')];
  const selected = data.screens.map(() => 0);
  const versions = data.screens.map(() => 0);
  const dialog = document.getElementById('product-dialog');
  const modalImage = dialog.querySelector('img');
  const modalTitle = dialog.querySelector('h3');
  const modalCounter = dialog.querySelector('.product-counter');
  let active = 0;
  let opener = null;
  let modalApp = 0;
  let suppressClick = false;
  const count = (i) => `${String(selected[i] + 1).padStart(2, '0')} / ${String(data.screens[i].length).padStart(2, '0')}`;

  function updateModal(i) {
    const shot = data.screens[i][selected[i]];
    modalImage.src = shot.src;
    modalImage.alt = `${data.fullnames[i]} — ${shot.label}`;
    modalImage.width = shot.width;
    modalImage.height = shot.height;
    modalTitle.textContent = `${data.fullnames[i]} — ${shot.label}`;
    modalCounter.textContent = count(i);
  }
  function selectApp(index, focus = false) {
    active = index;
    tabs.forEach((tab, i) => {
      tab.setAttribute('role', 'tab');
      tab.setAttribute('aria-selected', String(i === index));
      tab.tabIndex = i === index ? 0 : -1;
      panels[i].hidden = i !== index;
      panels[i].setAttribute('role', 'tabpanel');
    });
    if (focus) tabs[index].focus({preventScroll: true});
  }
  async function selectScreen(i, requested, reveal = true) {
    const items = data.screens[i];
    const n = (requested + items.length) % items.length;
    selected[i] = n;
    const version = ++versions[i];
    const shot = items[n];
    const panel = panels[i];
    const frame = panel.querySelector('.product-frame');
    const img = frame.querySelector('img');
    const error = panel.querySelector('.product-error');
    error.hidden = true;
    frame.setAttribute('aria-busy', 'true');
    const preload = new Image();
    preload.src = shot.src;
    try { await preload.decode(); } catch (_) {
      if (version === versions[i]) {
        frame.setAttribute('aria-busy', 'false');
        error.hidden = false;
      }
      return;
    }
    if (version !== versions[i]) return;
    img.src = shot.src;
    img.alt = `${data.fullnames[i]} — ${shot.label}`;
    img.width = shot.width;
    img.height = shot.height;
    frame.href = shot.src;
    frame.setAttribute('aria-label', `${data.ui.expand}: ${shot.label}`);
    frame.setAttribute('aria-busy', 'false');
    panel.querySelector('.product-expand').href = shot.src;
    panel.querySelector('.product-caption h4').textContent = shot.label;
    panel.querySelector('.product-caption p').textContent = shot.caption;
    panel.querySelector('.product-counter').textContent = count(i);
    panel.querySelector('.gallery-status').textContent = `${data.fullnames[i]} — ${shot.label}. ${n + 1} ${data.ui.of} ${items.length}.`;
    const thumbs = [...panel.querySelectorAll('.product-thumb')];
    thumbs.forEach((thumb, j) => thumb.setAttribute('aria-current', String(j === n)));
    if (reveal) {
      const rail = panel.querySelector('.product-thumbs');
      const thumb = thumbs[n];
      const left = thumb.offsetLeft - rail.offsetLeft;
      if (left < rail.scrollLeft) rail.scrollLeft = left;
      else if (left + thumb.offsetWidth > rail.scrollLeft + rail.clientWidth) rail.scrollLeft = left + thumb.offsetWidth - rail.clientWidth;
    }
    if (dialog.open && modalApp === i) updateModal(i);
    const next = new Image();
    next.src = items[(n + 1) % items.length].src;
  }
  function step(i, delta) { return selectScreen(i, selected[i] + delta); }
  function openScreen(i, element, event) {
    if (event && (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey)) return;
    if (typeof dialog.showModal !== 'function') return;
    if (event) event.preventDefault();
    if (suppressClick) { suppressClick = false; return; }
    modalApp = i;
    opener = element;
    dialog.classList.remove('is-zoomed');
    dialog.querySelector('[data-zoom]').setAttribute('aria-pressed', 'false');
    updateModal(i);
    if (!dialog.open) dialog.showModal();
  }
  tabs.forEach((tab, i) => {
    tab.addEventListener('click', e => { e.preventDefault(); selectApp(i); });
    tab.addEventListener('keydown', e => {
      let n;
      if (e.key === 'ArrowRight') n = (i + 1) % tabs.length;
      else if (e.key === 'ArrowLeft') n = (i + tabs.length - 1) % tabs.length;
      else if (e.key === 'Home') n = 0;
      else if (e.key === 'End') n = tabs.length - 1;
      else return;
      e.preventDefault(); selectApp(n, true);
    });
  });
  panels.forEach((panel, i) => {
    panel.querySelector('[data-prev]').addEventListener('click', () => step(i, -1));
    panel.querySelector('[data-next]').addEventListener('click', () => step(i, 1));
    panel.querySelectorAll('.product-thumb').forEach((thumb, j) => {
      thumb.addEventListener('click', e => {
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        e.preventDefault(); selectScreen(i, j);
      });
    });
    panel.querySelectorAll('.product-frame,.product-expand').forEach(el => el.addEventListener('click', e => openScreen(i, el, e)));
    panel.addEventListener('keydown', e => {
      if (e.target.matches('input,textarea,select') || e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.key === 'ArrowRight') { e.preventDefault(); step(i, 1); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); step(i, -1); }
      else if (e.key === 'Home') { e.preventDefault(); selectScreen(i, 0); }
      else if (e.key === 'End') { e.preventDefault(); selectScreen(i, data.screens[i].length - 1); }
    });
    const frame = panel.querySelector('.product-frame');
    let start = null;
    frame.addEventListener('pointerdown', e => { if (e.pointerType !== 'mouse') { suppressClick = false; start = {x:e.clientX,y:e.clientY}; } });
    frame.addEventListener('pointercancel', () => { start = null; });
    frame.addEventListener('pointerup', e => {
      if (!start) return;
      const dx = e.clientX - start.x, dy = e.clientY - start.y;
      start = null;
      if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.3) {
        suppressClick = true; step(i, dx < 0 ? 1 : -1);
        window.setTimeout(() => { suppressClick = false; }, 450);
      }
    });
  });
  dialog.querySelector('[data-close]').addEventListener('click', () => dialog.close());
  dialog.querySelector('[data-prev]').addEventListener('click', () => step(modalApp, -1));
  dialog.querySelector('[data-next]').addEventListener('click', () => step(modalApp, 1));
  dialog.querySelector('[data-zoom]').addEventListener('click', e => {
    const on = dialog.classList.toggle('is-zoomed');
    e.currentTarget.setAttribute('aria-pressed', String(on));
  });
  dialog.addEventListener('close', () => { if (opener) opener.focus({preventScroll:true}); });
  dialog.addEventListener('click', e => { if (e.target === dialog) { const box=dialog.getBoundingClientRect(); if(e.clientX<box.left||e.clientX>box.right||e.clientY<box.top||e.clientY>box.bottom) dialog.close(); } });
  dialog.addEventListener('keydown', e => {
    if (e.key === 'ArrowRight') { e.preventDefault(); step(modalApp, 1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); step(modalApp, -1); }
  });
  document.querySelectorAll('.lang a').forEach(a => a.addEventListener('click', () => { if (location.hash) a.hash=location.hash; }));
  root.querySelector('.product-tabs').setAttribute('role','tablist');
  const initial = data.keys.findIndex(key => location.hash === `#app-panel-${key}`);
  selectApp(initial >= 0 ? initial : 0);
})();
