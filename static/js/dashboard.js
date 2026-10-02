/**
 * Dashboard JavaScript – Requirements 22.1-22.7
 * Handles real-time XP updates, stat allocation, and daily quest display.
 */
'use strict';

const API = '/api';
let _refreshTimer;

async function apiFetch(url, opts = {}) {
  const res = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

function el(id) { return document.getElementById(id); }

// ── Load Player ─────────────────────────────────────────────
async function loadPlayer() {
  try {
    const p = await apiFetch(`${API}/player/${PLAYER_ID}`);
    updatePlayerUI(p);
    loadDailyQuests();
  } catch (e) {
    console.error('Failed to load player:', e);
  }
}

function updatePlayerUI(p) {
  el('playerName').textContent  = p.username;
  el('playerTitle').textContent = p.active_title ? p.active_title.name : '';
  el('playerRank').textContent  = `${p.rank}-Rank`;
  el('playerRank').className    = `dash__rank rank--${p.rank}`;
  el('playerGold').textContent  = `🪙 ${p.gold.toLocaleString()}`;
  el('playerLevel').textContent = p.level;

  // XP bar
  const xpReq = Math.round(100 * Math.pow(p.level + 1, 1.5));
  const pct = Math.min(100, Math.round((p.xp / xpReq) * 100));
  el('xpText').textContent        = `${p.xp.toLocaleString()} / ${xpReq.toLocaleString()} XP`;
  el('xpFill').style.width        = `${pct}%`;
  el('xpBar').setAttribute('aria-valuenow', pct);

  // HP / MP
  const maxHp = 100 + p.vit_stat * 10;
  const maxMp = 50  + p.int_stat * 5;
  el('hpFill').style.width = `${Math.min(100, Math.round((p.hp / maxHp) * 100))}%`;
  el('mpFill').style.width = `${Math.min(100, Math.round((p.mp / maxMp) * 100))}%`;
  el('hpText').textContent = `${p.hp} / ${maxHp}`;
  el('mpText').textContent = `${p.mp} / ${maxMp}`;

  // Stats
  const statsMap = { str: 'str_stat', int: 'int_stat', agi: 'agi_stat', vit: 'vit_stat', sen: 'sen_stat', luk: 'luk_stat' };
  Object.entries(statsMap).forEach(([key, field]) => {
    const e = el(`stat-${key}`);
    if (e) e.textContent = p[field];
  });

  // Stat allocation panel
  const badge = el('statPointsBadge');
  const panel = el('statAllocPanel');
  if (badge) badge.textContent = `${p.stat_points} point${p.stat_points !== 1 ? 's' : ''} available`;
  if (panel) panel.hidden = p.stat_points <= 0;
}

// ── Stat Allocation ─────────────────────────────────────────
async function allocateStat(statName) {
  try {
    await apiFetch(`${API}/player/${PLAYER_ID}/stats/allocate`, {
      method: 'POST',
      body: JSON.stringify({ stat_name: statName }),
    });
    await loadPlayer(); // Refresh UI with updated stats
  } catch (e) {
    console.error('Stat allocation failed:', e);
  }
}
window.allocateStat = allocateStat;

// ── Daily Quests ─────────────────────────────────────────────
async function loadDailyQuests() {
  try {
    const data = await apiFetch(`${API}/quests/daily?player_id=${PLAYER_ID}`);
    renderDailyQuests(data.quests || []);
  } catch (e) {
    console.error('Failed to load daily quests:', e);
  }
}

function renderDailyQuests(quests) {
  const list = el('dailyQuestList');
  if (!list) return;
  if (!quests.length) {
    list.innerHTML = '<li style="color:var(--clr-muted);padding:.5rem 0">No daily quests today. Check back at midnight!</li>';
    return;
  }
  list.innerHTML = quests.map(q => `
    <li class="dash__quest-item">
      <div class="dash__quest-check ${q.status === 'completed' ? 'dash__quest-check--done' : ''}"
           onclick="completeQuest(${q.id})"
           role="button" aria-label="Complete ${escHtml(q.title)}"
           tabindex="0"></div>
      <span class="dash__quest-name ${q.status === 'completed' ? 'quest--done' : ''}">${escHtml(q.title)}</span>
      <span class="dash__quest-xp">+${q.xp_reward} XP</span>
    </li>`).join('');
}

async function completeQuest(questId) {
  try {
    const result = await apiFetch(`${API}/quests/${questId}/complete`, {
      method: 'POST',
      body: JSON.stringify({ player_id: PLAYER_ID }),
    });
    if (result.success) {
      await loadPlayer();
      await loadDailyQuests();
    }
  } catch (e) {
    console.error('Quest completion failed:', e);
  }
}
window.completeQuest = completeQuest;

// ── Helpers ──────────────────────────────────────────────────
function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Auto-refresh every 10s ───────────────────────────────────
function startAutoRefresh() {
  _refreshTimer = setInterval(loadPlayer, 10_000);
}

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadPlayer();
  startAutoRefresh();
});
