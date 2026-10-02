/**
 * Quest Log JavaScript – Requirements 23.1-23.7
 */
'use strict';

const API = '/api';

function escHtml(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function el(id)     { return document.getElementById(id); }

async function apiFetch(url, opts = {}) {
  const res = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!res.ok) throw new Error(res.status);
  return res.json();
}

// ── Load All Quests ─────────────────────────────────────────
async function loadQuests() {
  try {
    const data = await apiFetch(`${API}/quests?player_id=${PLAYER_ID}`);
    render('dailyList',   data.daily     || [], renderDailyItem);
    render('mainList',    data.main      || [], renderMainItem);
    render('instantList', data.instant   || [], renderInstantItem);
    render('emergencyList',data.emergency|| [], renderQuestItem);

    // Daily completion %
    const daily = data.daily || [];
    if (daily.length) {
      const done = daily.filter(q => q.status === 'completed').length;
      el('dailyPct').textContent = Math.round(done / daily.length * 100) + '%';
    }
  } catch (e) { console.error('Load quests:', e); }
}

function render(listId, items, renderFn) {
  const list = el(listId);
  if (!list) return;
  if (!items.length) {
    list.innerHTML = '<li class="quest--empty">No quests here.</li>';
    return;
  }
  list.innerHTML = items.map(renderFn).join('');
  // Attach expand toggles
  list.querySelectorAll('.quest-item').forEach(item => {
    item.addEventListener('click', e => {
      if (e.target.closest('.btn')) return;
      item.classList.toggle('quest-item--open');
    });
  });
}

function isOverdue(q) { return q.deadline && new Date(q.deadline) < new Date() && q.status === 'active'; }

function renderQuestItem(q) {
  const overdue = isOverdue(q) ? 'quest-item--overdue' : '';
  const done    = q.status === 'completed' ? 'quest-item--completed' : '';
  return `
    <li class="quest-item ${overdue} ${done}" data-id="${q.id}">
      <div class="quest-item__header">
        <span class="badge badge--${q.status}">${escHtml(q.status)}</span>
        <span class="quest-item__title">${escHtml(q.title)}</span>
        <span class="quest-item__xp">+${q.xp_reward} XP</span>
        <span class="quest-item__expand">▼</span>
      </div>
      <div class="quest-item__body">
        <p>${escHtml(q.description || '')}</p>
        ${q.status === 'active' ? `<div class="quest-item__complete"><button class="btn btn--primary" onclick="completeQuest(${q.id}, event)">✓ Complete</button></div>` : ''}
      </div>
    </li>`;
}

function renderDailyItem(q) { return renderQuestItem(q); }

function renderMainItem(q) {
  const progress = q.progress || 0;
  const overdue  = isOverdue(q) ? 'quest-item--overdue' : '';
  const done     = q.status === 'completed' ? 'quest-item--completed' : '';
  return `
    <li class="quest-item ${overdue} ${done}" data-id="${q.id}">
      <div class="quest-item__header">
        <span class="badge badge--${q.status}">${escHtml(q.status)}</span>
        <span class="quest-item__title">${escHtml(q.title)}</span>
        <span class="quest-item__xp">+${q.xp_reward} XP</span>
        <span class="quest-item__expand">▼</span>
      </div>
      <div class="quest-item__progress">
        <div class="progress" aria-label="Progress ${progress}%"><div class="progress__fill" style="width:${progress}%"></div></div>
      </div>
      <div class="quest-item__body">
        <p>${escHtml(q.description || '')}</p>
        ${q.status === 'active' ? `<div class="quest-item__complete"><button class="btn btn--primary" onclick="completeQuest(${q.id}, event)">✓ Complete</button></div>` : ''}
      </div>
    </li>`;
}

function renderInstantItem(q) {
  const deadline = q.deadline ? new Date(q.deadline) : null;
  const remaining = deadline ? Math.max(0, Math.round((deadline - Date.now()) / 1000)) : 0;
  const mins = Math.floor(remaining / 60), secs = remaining % 60;
  const timerHtml = q.status === 'active'
    ? `<span class="quest-item__timer" data-deadline="${q.deadline}">⏱ ${mins}m ${secs}s</span>`
    : '';
  return `
    <li class="quest-item" data-id="${q.id}">
      <div class="quest-item__header">
        <span class="badge badge--${q.status}">${escHtml(q.status)}</span>
        <span class="quest-item__title">${escHtml(q.title)}</span>
        ${timerHtml}
        <span class="quest-item__xp">+${q.xp_reward} XP</span>
      </div>
      <div class="quest-item__body">
        <p>${escHtml(q.description || '')}</p>
        ${q.status === 'active' ? `<div class="quest-item__complete"><button class="btn btn--primary" onclick="completeQuest(${q.id}, event)">✓ Complete</button></div>` : ''}
      </div>
    </li>`;
}

// ── Complete Quest ─────────────────────────────────────────
async function completeQuest(questId, event) {
  event.stopPropagation();
  try {
    const result = await apiFetch(`${API}/quests/${questId}/complete`, {
      method: 'POST',
      body: JSON.stringify({ player_id: PLAYER_ID }),
    });
    if (result.success) loadQuests();
  } catch (e) { console.error('Complete quest:', e); }
}
window.completeQuest = completeQuest;

// ── Countdown Timer ─────────────────────────────────────────
function tickTimers() {
  document.querySelectorAll('[data-deadline]').forEach(el => {
    const deadline = new Date(el.dataset.deadline);
    const remaining = Math.max(0, Math.round((deadline - Date.now()) / 1000));
    const mins = Math.floor(remaining / 60), secs = remaining % 60;
    el.textContent = `⏱ ${mins}m ${String(secs).padStart(2,'0')}s`;
    if (remaining === 0) loadQuests();
  });
}

document.addEventListener('DOMContentLoaded', () => {
  loadQuests();
  setInterval(tickTimers, 1000);
  setInterval(loadQuests, 30_000);
});
