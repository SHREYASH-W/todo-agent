/**
 * LifeHunter Dashboard – fully working UI
 * All buttons functional, real API calls, auto-refresh
 */
'use strict';

const API = '/api';
let _refreshTimer = null;
let _pendingStatAlloc = null;
let _playerCache = null;

// ── API Helper ──────────────────────────────────────────────
async function api(url, opts = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

function el(id) { return document.getElementById(id); }

// ── Load Player ─────────────────────────────────────────────
async function loadPlayer() {
  try {
    const p = await api(`${API}/player/${PLAYER_ID}`);
    _playerCache = p;
    renderPlayer(p);
    loadDailyQuests();
  } catch (e) {
    console.error('Load player:', e);
  }
}

function renderPlayer(p) {
  el('playerName').textContent = p.username || 'Hunter';
  el('playerTitle').textContent = p.active_title?.name || '';
  el('playerRank').textContent  = `${p.rank}-Rank`;
  el('playerRank').className    = `dash__rank rank--${p.rank}`;
  el('playerGold').textContent  = (p.gold || 0).toLocaleString();
  el('playerLevel').textContent = p.level;
  el('xpLevel').textContent     = p.level;

  // XP bar
  const xpReq = Math.round(100 * Math.pow(p.level + 1, 1.5));
  const pct   = p.level >= 999 ? 100 : Math.min(100, Math.round((p.xp / xpReq) * 100));
  el('xpText').textContent = `${(p.xp || 0).toLocaleString()} / ${xpReq.toLocaleString()} XP`;
  el('xpPct').textContent  = `${pct}%`;
  el('xpFill').style.width = `${pct}%`;
  el('xpBar').setAttribute('aria-valuenow', pct);

  // HP / MP
  const maxHp = 100 + (p.vit_stat || 10) * 10;
  const maxMp = 50  + (p.int_stat || 10) * 5;
  const hpPct = Math.min(100, Math.round((p.hp / maxHp) * 100));
  const mpPct = Math.min(100, Math.round((p.mp / maxMp) * 100));
  el('hpFill').style.width = `${hpPct}%`;
  el('mpFill').style.width = `${mpPct}%`;
  el('hpText').textContent = `${p.hp} / ${maxHp}`;
  el('mpText').textContent = `${p.mp} / ${maxMp}`;

  // Stats
  const statMap = { str: 'str_stat', int: 'int_stat', agi: 'agi_stat', vit: 'vit_stat', sen: 'sen_stat', luk: 'luk_stat' };
  Object.entries(statMap).forEach(([key, field]) => {
    const e = el(`stat-${key}`);
    if (e) e.textContent = p[field] ?? 10;
  });

  // Stat points
  const pts = p.stat_points || 0;
  const badge = el('statPointsBadge');
  const hint  = el('statHint');
  if (badge) { badge.style.display = pts > 0 ? 'inline-flex' : 'none'; }
  if (hint)  { hint.style.display  = pts > 0 ? 'block' : 'none'; }
  el('statPointsCount').textContent = pts;

  // Stat items – highlight if points available
  document.querySelectorAll('.stat-item').forEach(item => {
    item.style.cursor = pts > 0 ? 'pointer' : 'default';
    item.style.opacity = pts > 0 ? '1' : '0.85';
  });
}

// ── Stat Allocation ─────────────────────────────────────────
const STAT_LABELS = {
  str_stat: 'Strength (STR) – increases physical power',
  int_stat: 'Intelligence (INT) – increases MP by 5 per point',
  agi_stat: 'Agility (AGI) – increases speed and evasion',
  vit_stat: 'Vitality (VIT) – increases HP by 10 per point',
  sen_stat: 'Sense (SEN) – improves perception',
  luk_stat: 'Luck (LUK) – improves rare rewards',
};

function openStatAlloc(statName) {
  const pts = _playerCache?.stat_points || 0;
  if (pts <= 0) {
    showToast('No stat points available. Level up to earn more!', 'info');
    return;
  }
  _pendingStatAlloc = statName;
  el('statModalDesc').textContent = `${STAT_LABELS[statName] || statName}\n\nYou have ${pts} point${pts !== 1 ? 's' : ''} available.`;
  el('statModal').hidden = false;
}
window.openStatAlloc = openStatAlloc;

function closeStatModal() {
  el('statModal').hidden = true;
  _pendingStatAlloc = null;
}
window.closeStatModal = closeStatModal;

async function confirmStatAlloc() {
  if (!_pendingStatAlloc) return;
  const btn = el('statAllocConfirmBtn');
  btn.disabled = true;
  btn.textContent = 'Allocating…';
  try {
    const res = await api(`${API}/player/${PLAYER_ID}/stats/allocate`, {
      method: 'POST',
      body: JSON.stringify({ stat_name: _pendingStatAlloc }),
    });
    closeStatModal();
    showToast(`✅ +1 ${_pendingStatAlloc.replace('_stat','').toUpperCase()} allocated!`, 'success');
    await loadPlayer();
  } catch (e) {
    showToast(`❌ ${e.message}`, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '+ Allocate Point';
  }
}
window.confirmStatAlloc = confirmStatAlloc;

// ── Daily Quests ─────────────────────────────────────────────
async function loadDailyQuests() {
  const container = el('dailyQuestList');
  if (!container) return;

  try {
    const data = await api(`${API}/quests/daily?player_id=${PLAYER_ID}`);
    const quests = data.quests || [];

    if (!quests.length) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-state__icon">🌙</div>
          <div class="empty-state__text">No daily quests yet.<br/>Click "Generate Daily Quests" to start!</div>
        </div>`;
      el('dailyPct').textContent = '0%';
      return;
    }

    const done = quests.filter(q => q.status === 'completed').length;
    const pct  = Math.round((done / quests.length) * 100);
    el('dailyPct').textContent = `${done}/${quests.length} (${pct}%)`;

    container.innerHTML = quests.map(q => `
      <div class="quest-row ${q.status === 'completed' ? 'quest-row--done' : ''}" data-id="${q.id}">
        <div class="quest-row__check ${q.status === 'completed' ? 'quest-row__check--done' : ''}"
             onclick="completeDailyQuest(${q.id})"
             role="checkbox" aria-checked="${q.status === 'completed'}"
             aria-label="Complete: ${esc(q.title)}" tabindex="0"
             onkeydown="if(event.key==='Enter'||event.key===' ')completeDailyQuest(${q.id})">
          ${q.status === 'completed' ? '✓' : ''}
        </div>
        <div class="quest-row__info">
          <span class="quest-row__title">${esc(q.title)}</span>
          <span class="quest-row__desc">${esc(q.description || '')}</span>
        </div>
        <div class="quest-row__xp">+${q.xp_reward} XP</div>
      </div>`).join('');

    // Generate button visibility
    const genBtn = el('generateQuestsBtn');
    if (genBtn) genBtn.style.display = 'none';

  } catch (e) {
    container.innerHTML = `<div class="empty-state"><div class="empty-state__text">⚠️ Failed to load quests</div></div>`;
  }
}

async function completeDailyQuest(questId) {
  // Optimistic update
  const row = document.querySelector(`[data-id="${questId}"]`);
  if (row) row.style.opacity = '.5';

  try {
    const result = await api(`${API}/quests/${questId}/complete`, {
      method: 'POST',
      body: JSON.stringify({ player_id: PLAYER_ID }),
    });
    if (result.success) {
      const xpTotal = (result.xp_awarded || 0) + (result.bonus_xp || 0);
      showToast(`✅ Quest complete! +${xpTotal} XP${result.bonus_xp ? ' 🎉 Bonus!' : ''}`, 'success');
      await loadPlayer();
    }
  } catch (e) {
    if (row) row.style.opacity = '1';
    showToast(`❌ ${e.message}`, 'error');
  }
}
window.completeDailyQuest = completeDailyQuest;

async function generateDailyQuests() {
  const btn = el('generateQuestsBtn');
  if (btn) { btn.disabled = true; btn.textContent = '🎲 Generating…'; }
  try {
    const res = await api(`${API}/player/${PLAYER_ID}/quests/generate-daily`, { method: 'POST' });
    if (res.generated) {
      showToast(`✅ Generated ${res.count} daily quests!`, 'success');
    } else {
      showToast('Daily quests already exist for today', 'info');
    }
    await loadDailyQuests();
  } catch (e) {
    showToast(`❌ ${e.message}`, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '🎲 Generate Daily Quests'; }
  }
}
window.generateDailyQuests = generateDailyQuests;

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadPlayer();
  // Auto-refresh every 15s
  _refreshTimer = setInterval(loadPlayer, 15_000);

  // Close stat modal on overlay click
  el('statModal')?.addEventListener('click', e => {
    if (e.target === el('statModal')) closeStatModal();
  });
});
