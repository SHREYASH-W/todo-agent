/**
 * Achievement Gallery JavaScript – Requirements 25.1-25.7
 */
'use strict';
let _allAchievements = [];
function escHtml(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
const RARITY_ICONS = {common:'🔵',rare:'💎',epic:'💜',legendary:'⭐'};

async function loadAchievements() {
  const r = await fetch(`/api/player/${PLAYER_ID}/achievements`);
  if(!r.ok) return;
  const data = await r.json();
  _allAchievements = data.achievements || [];
  updatePct(_allAchievements);
  renderGrid(_allAchievements);
}

function updatePct(achs) {
  const total   = achs.length;
  const unlocked = achs.filter(a=>a.unlocked).length;
  const pct = total ? Math.round(unlocked/total*100) : 0;
  document.getElementById('achPct').textContent = pct+'%';
}

function renderGrid(achs) {
  const grid = document.getElementById('achGrid');
  grid.innerHTML = achs.map(a => {
    const locked  = a.unlocked ? '' : 'ach-card--locked';
    const dateHtml = a.unlocked_at ? `<div class="ach-card__date">${new Date(a.unlocked_at).toLocaleDateString()}</div>` : '';
    return `
      <div class="ach-card ach-card--${a.rarity} ${locked}" role="listitem"
           tabindex="0" onclick="openModal(${a.id})" onkeydown="if(event.key==='Enter')openModal(${a.id})"
           aria-label="${escHtml(a.name)}" data-rarity="${a.rarity}">
        <div class="ach-card__icon">${RARITY_ICONS[a.rarity]||'🏆'}</div>
        <div class="ach-card__name">${escHtml(a.name)}</div>
        <div class="ach-card__rarity"><span class="badge badge--${a.rarity}">${a.rarity}</span></div>
        ${dateHtml}
      </div>`;
  }).join('');
}

function openModal(id) {
  const a = _allAchievements.find(x=>x.id===id);
  if(!a) return;
  let bonusHtml = '';
  try {
    const b = JSON.parse(a.stat_bonus||'{}');
    const entries = Object.entries(b);
    if(entries.length) bonusHtml = '<p><strong>Bonus:</strong> '+entries.map(([k,v])=>`${k} +${v}`).join(', ')+'</p>';
  } catch(_){}
  document.getElementById('achModalContent').innerHTML = `
    <h2 id="achModalTitle" style="color:var(--clr-primary)">${escHtml(a.name)}</h2>
    <p style="margin:.5rem 0;color:var(--clr-muted)">${escHtml(a.description)}</p>
    <span class="badge badge--${a.rarity}">${a.rarity}</span>
    ${bonusHtml}
    ${a.unlocked_at ? `<p style="font-size:.8rem;color:var(--clr-muted);margin-top:.5rem">Unlocked: ${new Date(a.unlocked_at).toLocaleDateString()}</p>` : '<p style="color:var(--clr-muted);font-size:.85rem;margin-top:.5rem">🔒 Locked</p>'}`;
  document.getElementById('achModal').hidden = false;
}
function closeModal() { document.getElementById('achModal').hidden = true; }
window.openModal  = openModal;
window.closeModal = closeModal;

// Filters
document.addEventListener('DOMContentLoaded', () => {
  loadAchievements();
  document.querySelectorAll('[data-filter]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-filter]').forEach(b=>b.classList.remove('ach-filter--active'));
      btn.classList.add('ach-filter--active');
      const f = btn.dataset.filter;
      renderGrid(f==='all' ? _allAchievements : _allAchievements.filter(a=>a.rarity===f));
    });
  });
});
