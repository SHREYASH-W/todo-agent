/**
 * Quest Log – fully functional with create, complete, delete, tabs, timers
 */
'use strict';

const API = '/api';
let _allQuests = { daily: [], main: [], instant: [], emergency: [] };
let _currentTab = 'daily';
let _createType = 'main';
let _timerInterval = null;

// ── API ─────────────────────────────────────────────────────
async function api(url, opts = {}) {
  const res = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || `HTTP ${res.status}`); }
  return res.json();
}

// ── Load All Quests ─────────────────────────────────────────
async function loadQuests() {
  try {
    const data = await api(`${API}/quests?player_id=${PLAYER_ID}`);
    _allQuests = {
      daily:     data.daily     || [],
      main:      data.main      || [],
      instant:   data.instant   || [],
      emergency: data.emergency || [],
    };

    // Counts
    ['daily','main','instant','emergency'].forEach(t => {
      const cnt = document.getElementById(`${t}Cnt`);
      if (cnt) {
        const n = (_allQuests[t] || []).length;
        cnt.textContent = n || '';
        cnt.style.display = n ? 'inline-flex' : 'none';
      }
    });

    // Daily pct
    const daily = _allQuests.daily;
    if (daily.length) {
      const done = daily.filter(q => q.status === 'completed').length;
      const pct  = Math.round(done / daily.length * 100);
      const el   = document.getElementById('dailyPct');
      if (el) el.textContent = `${done}/${daily.length} (${pct}%)`;
    }

    renderCurrentTab();
  } catch (e) {
    showToast('Failed to load quests', 'error');
  }
}

// ── Tab switching ───────────────────────────────────────────
function switchTab(tab) {
  _currentTab = tab;
  document.querySelectorAll('.ql-tab').forEach(b => b.classList.remove('ql-tab--active'));
  document.querySelectorAll('.ql-panel').forEach(p => p.hidden = true);
  document.querySelector(`[data-tab="${tab}"]`)?.classList.add('ql-tab--active');
  const panel = document.getElementById(`panel-${tab}`);
  if (panel) panel.hidden = false;
  renderCurrentTab();
}
window.switchTab = switchTab;

function renderCurrentTab() {
  renderQuests(_currentTab, _allQuests[_currentTab] || []);
}

// ── Render quests ───────────────────────────────────────────
function renderQuests(type, quests) {
  const container = document.getElementById(`list-${type}`);
  if (!container) return;

  if (!quests.length) {
    container.innerHTML = `<div class="empty-state"><div class="empty-state__icon">${typeEmoji(type)}</div><div class="empty-state__text">No ${type} quests yet.</div></div>`;
    return;
  }

  container.innerHTML = quests.map(q => renderQuestItem(q, type)).join('');

  // Attach toggle events
  container.querySelectorAll('.quest-item__header').forEach(h => {
    h.addEventListener('click', e => {
      if (e.target.closest('button')) return;
      h.closest('.quest-item')?.classList.toggle('quest-item--open');
    });
  });
}

function typeEmoji(t) { return { daily:'⚡', main:'🗺️', instant:'⏱️', emergency:'🚨' }[t] || '📋'; }

function isOverdue(q) {
  return q.deadline && new Date(q.deadline) < new Date() && q.status === 'active';
}

function renderQuestItem(q, type) {
  const overdue = isOverdue(q) ? 'quest-item--overdue' : '';
  const done    = q.status === 'completed' ? 'quest-item--completed' : '';

  const timer = (type === 'instant' && q.status === 'active' && q.deadline)
    ? `<span class="quest-item__timer" data-deadline="${q.deadline}" id="timer-${q.id}">⏱ …</span>`
    : '';

  const progressBar = (type === 'main' && q.progress !== undefined)
    ? `<div class="quest-item__progress"><div class="progress progress--sm"><div class="progress__fill" style="width:${q.progress || 0}%"></div></div></div>`
    : '';

  const actions = q.status === 'active' ? `
    <div class="quest-item__actions">
      <button class="btn btn--primary btn--sm" onclick="completeQuest(${q.id}, event)">✓ Complete</button>
      <button class="btn btn--ghost btn--sm" onclick="deleteQuest(${q.id}, event)">🗑 Delete</button>
    </div>` : '';

  return `
    <div class="quest-item ${overdue} ${done}" data-id="${q.id}">
      <div class="quest-item__header">
        <span class="badge badge--${q.status}">${q.status}</span>
        <span class="quest-item__title">${esc(q.title)}</span>
        ${timer}
        <span class="quest-item__xp">+${q.xp_reward} XP</span>
        ${q.gold_reward ? `<span style="font-size:.8rem;color:var(--gold)">🪙${q.gold_reward}</span>` : ''}
        <span class="quest-item__expand">▾</span>
      </div>
      ${progressBar}
      <div class="quest-item__body">
        <p>${esc(q.description || 'No description.')}</p>
        ${q.difficulty ? `<span class="badge badge--${q.difficulty}">${q.difficulty}</span>` : ''}
        ${q.deadline ? `<p style="font-size:.8rem">⏰ Deadline: ${new Date(q.deadline).toLocaleString()}</p>` : ''}
        ${actions}
      </div>
    </div>`;
}

// ── Complete quest ──────────────────────────────────────────
async function completeQuest(questId, event) {
  event?.stopPropagation();
  const item = document.querySelector(`[data-id="${questId}"]`);
  if (item) item.style.opacity = '.5';

  try {
    const result = await api(`${API}/quests/${questId}/complete`, {
      method: 'POST',
      body: JSON.stringify({ player_id: PLAYER_ID }),
    });
    if (result.success) {
      const total = (result.xp_awarded || 0) + (result.bonus_xp || 0);
      showToast(`✅ +${total} XP${result.bonus_xp ? ' 🎉 Bonus!' : ''}`, 'success');
      await loadQuests();
    } else {
      showToast(result.message || 'Could not complete quest', 'error');
      if (item) item.style.opacity = '1';
    }
  } catch (e) {
    showToast(`❌ ${e.message}`, 'error');
    if (item) item.style.opacity = '1';
  }
}
window.completeQuest = completeQuest;

// ── Delete quest ────────────────────────────────────────────
async function deleteQuest(questId, event) {
  event?.stopPropagation();
  if (!confirm('Delete this quest? This cannot be undone.')) return;

  try {
    await api(`${API}/quests/${questId}?player_id=${PLAYER_ID}`, { method: 'DELETE' });
    showToast('Quest deleted', 'info');
    await loadQuests();
  } catch (e) {
    showToast(`❌ ${e.message}`, 'error');
  }
}
window.deleteQuest = deleteQuest;

// ── Generate daily ──────────────────────────────────────────
async function generateDaily() {
  try {
    const res = await api(`${API}/player/${PLAYER_ID}/quests/generate-daily`, { method: 'POST' });
    showToast(res.generated ? `🎲 ${res.count} daily quests generated!` : 'Daily quests already exist', res.generated ? 'success' : 'info');
    await loadQuests();
  } catch (e) {
    showToast(`❌ ${e.message}`, 'error');
  }
}
window.generateDaily = generateDaily;

// ── Create quest modal ──────────────────────────────────────
function openCreateModal(type = 'main') {
  _createType = type;
  document.getElementById('qType').value = type;
  document.getElementById('createModalTitle').textContent =
    { main: 'New Main Quest', instant: '⚡ Start Instant Dungeon', emergency: '🚨 Emergency Quest' }[type] || 'New Quest';
  document.getElementById('durationGroup').hidden = (type !== 'instant');
  document.getElementById('createModal').hidden = false;
}
window.openCreateModal = openCreateModal;

function closeCreateModal() {
  document.getElementById('createModal').hidden = true;
  document.getElementById('createForm').reset();
}
window.closeCreateModal = closeCreateModal;

async function submitCreateQuest(event) {
  event.preventDefault();
  const btn = document.getElementById('createSubmitBtn');
  btn.disabled = true; btn.textContent = 'Creating…';

  const type = document.getElementById('qType').value;
  const body = {
    player_id:   PLAYER_ID,
    quest_type:  type,
    title:       document.getElementById('qTitle').value.trim(),
    description: document.getElementById('qDesc').value.trim(),
    xp_reward:   parseInt(document.getElementById('qXp').value) || 50,
    gold_reward: parseInt(document.getElementById('qGold').value) || 20,
    difficulty:  document.getElementById('qDiff').value,
  };

  if (type === 'instant') {
    const mins = parseInt(document.getElementById('qDuration').value) || 60;
    body.duration_minutes = Math.max(15, Math.min(240, mins));
  }

  try {
    await api(`${API}/quests`, { method: 'POST', body: JSON.stringify(body) });
    showToast('✅ Quest created!', 'success');
    closeCreateModal();
    await loadQuests();
    switchTab(type === 'instant' ? 'instant' : type === 'emergency' ? 'emergency' : 'main');
  } catch (e) {
    showToast(`❌ ${e.message}`, 'error');
  } finally {
    btn.disabled = false; btn.textContent = 'Create Quest';
  }
}
window.submitCreateQuest = submitCreateQuest;

// ── Countdown timers ────────────────────────────────────────
function tickTimers() {
  document.querySelectorAll('[data-deadline]').forEach(el => {
    const remaining = Math.max(0, Math.round((new Date(el.dataset.deadline) - Date.now()) / 1000));
    const h = Math.floor(remaining / 3600);
    const m = Math.floor((remaining % 3600) / 60);
    const s = remaining % 60;
    el.textContent = h > 0
      ? `⏱ ${h}h ${m}m`
      : `⏱ ${m}m ${String(s).padStart(2,'0')}s`;
    if (remaining === 0) { el.style.color = 'var(--danger)'; }
  });
}

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadQuests();
  _timerInterval = setInterval(tickTimers, 1000);
  setInterval(loadQuests, 30_000);

  // Close modal on overlay click
  document.getElementById('createModal')?.addEventListener('click', e => {
    if (e.target.id === 'createModal') closeCreateModal();
  });
});
