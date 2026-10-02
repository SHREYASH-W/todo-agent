/**
 * Achievements Gallery – filter, modal, real API data
 */
'use strict';

let _all = [];
let _filter = 'all';

const RARITY = { common: '🔵', rare: '💎', epic: '💜', legendary: '⭐' };

async function loadAchievements() {
  const grid = document.getElementById('achGrid');
  grid.innerHTML = '<div class="loading-text"><div class="spinner"></div></div>';

  try {
    const data = await (await fetch(`/api/player/${PLAYER_ID}/achievements`)).json();
    _all = data.achievements || [];
    renderStats(data);
    applyFilter();
  } catch (e) {
    grid.innerHTML = `<div class="empty-state"><div class="empty-state__text">⚠️ Failed to load</div></div>`;
  }
}

function renderStats(data) {
  const row = document.getElementById('achStats');
  if (!row) return;
  const unlocked = data.unlocked || 0;
  const total    = data.total    || 0;
  const pct      = data.completion_pct || 0;

  // Update header badge + bar
  const badge = document.getElementById('achPct');
  const bar   = document.getElementById('achProgressBar');
  if (badge) badge.textContent = `${pct}%`;
  if (bar)   bar.style.width   = `${pct}%`;

  // Stats row
  const byRarity = { common: 0, rare: 0, epic: 0, legendary: 0 };
  _all.filter(a => a.unlocked).forEach(a => { if (byRarity[a.rarity] !== undefined) byRarity[a.rarity]++; });

  row.innerHTML = [
    `<div class="ach-stat-chip">✅ ${unlocked}/${total} unlocked</div>`,
    ...Object.entries(byRarity).filter(([,v]) => v > 0).map(([r,v]) => `<div class="ach-stat-chip">${RARITY[r]} ${v} ${r}</div>`),
  ].join('');
}

function applyFilter() {
  let list = _all;
  if (_filter === 'unlocked') list = _all.filter(a => a.unlocked);
  else if (_filter !== 'all') list = _all.filter(a => a.rarity === _filter);
  renderGrid(list);
}

function renderGrid(list) {
  const grid = document.getElementById('achGrid');
  if (!list.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><div class="empty-state__icon">🏆</div><div class="empty-state__text">No achievements found.</div></div>`;
    return;
  }
  grid.innerHTML = list.map(a => `
    <div class="ach-card ach-card--${a.rarity} ${a.unlocked ? '' : 'ach-card--locked'}"
         role="listitem" tabindex="0"
         onclick="openAchModal(${a.id})"
         onkeydown="if(event.key==='Enter'||event.key===' ')openAchModal(${a.id})"
         aria-label="${esc(a.name)}" data-rarity="${a.rarity}">
      ${!a.unlocked ? '<span class="ach-card__lock">🔒</span>' : ''}
      <div class="ach-card__icon">${RARITY[a.rarity] || '🏆'}</div>
      <div class="ach-card__name">${esc(a.name)}</div>
      <span class="badge badge--${a.rarity}">${a.rarity}</span>
      ${a.unlocked_at ? `<div class="ach-card__date">${new Date(a.unlocked_at).toLocaleDateString()}</div>` : ''}
    </div>`).join('');
}

function openAchModal(id) {
  const a = _all.find(x => x.id === id);
  if (!a) return;

  let bonusHtml = '';
  try {
    const b = JSON.parse(a.stat_bonus || '{}');
    const entries = Object.entries(b);
    if (entries.length) {
      bonusHtml = `<div style="margin:.75rem 0;padding:.75rem;background:rgba(0,204,102,.08);border:1px solid rgba(0,204,102,.2);border-radius:8px;font-size:.88rem">
        <strong style="color:var(--success)">🎁 Bonus:</strong> ${entries.map(([k,v]) => `${k.replace('_stat','').toUpperCase()} +${v}`).join(' · ')}
      </div>`;
    }
  } catch (_) {}

  document.getElementById('achModalContent').innerHTML = `
    <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:1rem">
      <span style="font-size:3rem">${RARITY[a.rarity] || '🏆'}</span>
      <div>
        <h2 style="font-size:1.2rem;font-weight:800">${esc(a.name)}</h2>
        <span class="badge badge--${a.rarity}">${a.rarity}</span>
      </div>
    </div>
    <p style="color:var(--muted);margin-bottom:.75rem;font-size:.9rem;line-height:1.6">${esc(a.description || 'No description.')}</p>
    ${bonusHtml}
    <div style="margin-top:1rem;font-size:.85rem;color:var(--muted)">
      ${a.unlocked
        ? `<span style="color:var(--success)">✅ Unlocked ${a.unlocked_at ? 'on ' + new Date(a.unlocked_at).toLocaleDateString() : ''}</span>`
        : `<span>🔒 Not yet unlocked</span>`}
    </div>
    <div style="margin-top:1.25rem">
      <button class="btn btn--ghost" onclick="closeAchModal()">Close</button>
    </div>`;
  document.getElementById('achModal').hidden = false;
}

function closeAchModal() { document.getElementById('achModal').hidden = true; }
window.openAchModal  = openAchModal;
window.closeAchModal = closeAchModal;

document.addEventListener('DOMContentLoaded', () => {
  loadAchievements();

  document.querySelectorAll('[data-filter]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-filter]').forEach(b => b.classList.remove('ach-filter--active'));
      btn.classList.add('ach-filter--active');
      _filter = btn.dataset.filter;
      applyFilter();
    });
  });

  document.getElementById('achModal')?.addEventListener('click', e => {
    if (e.target.id === 'achModal') closeAchModal();
  });
});
