/**
 * Skill Tree – fully functional unlock, allocate, tooltips, filter
 */
'use strict';

const API = '/api';
let _skills     = [];
let _available  = 0;
let _filterType = 'all';

async function apiCall(url, opts = {}) {
  const res = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!res.ok) { const e = await res.json().catch(()=>({})); throw new Error(e.error || `HTTP ${res.status}`); }
  return res.json();
}

// ── Load Skills ─────────────────────────────────────────────
async function loadSkills() {
  try {
    const data = await apiCall(`${API}/player/${PLAYER_ID}/skills`);
    _skills    = data.skills || [];
    _available = data.skill_points_available || 0;

    const badge = document.getElementById('skillPtsBadge');
    if (badge) {
      badge.textContent = `${_available} skill point${_available !== 1 ? 's' : ''} available`;
      badge.style.background = _available > 0 ? 'rgba(108,99,255,.2)' : 'rgba(0,212,255,.12)';
      badge.style.borderColor = _available > 0 ? 'rgba(108,99,255,.4)' : 'rgba(0,212,255,.3)';
      badge.style.color       = _available > 0 ? 'var(--primary-h)' : 'var(--accent)';
    }

    renderSkills();
  } catch (e) {
    document.getElementById('skillGrid').innerHTML = `<div class="empty-state"><div class="empty-state__text">⚠️ Failed to load skills</div></div>`;
  }
}

// ── Render ──────────────────────────────────────────────────
function renderSkills() {
  const grid = document.getElementById('skillGrid');
  const list = _filterType === 'all' ? _skills : _skills.filter(s => s.skill_type === _filterType);

  if (!list.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><div class="empty-state__icon">⚡</div><div class="empty-state__text">No skills found.</div></div>`;
    return;
  }

  grid.innerHTML = list.map(s => skillCard(s)).join('');
  grid.querySelectorAll('.skill-card').forEach(card => {
    card.addEventListener('mouseenter', showTip);
    card.addEventListener('mousemove',  moveTip);
    card.addEventListener('mouseleave', hideTip);
    card.addEventListener('click',      onCardClick);
    card.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') onCardClick.call(card, e); });
  });
}

function skillCard(s) {
  const isLocked    = !s.unlocked;
  const canUnlock   = s.can_unlock && !s.unlocked;
  const canAlloc    = s.unlocked && s.current_level < s.max_level && _available > 0;
  const isMaxed     = s.unlocked && s.current_level >= s.max_level;
  const pct         = s.max_level > 0 ? Math.round((s.current_level / s.max_level) * 100) : 0;
  const icon        = { active: '⚡', passive: '🛡️' }[s.skill_type] || '✦';
  const typeCls     = `skill-card__type-badge--${s.skill_type}`;

  return `
    <div class="skill-card ${isLocked ? 'skill-card--locked' : ''} ${isMaxed ? 'skill-card--maxed' : ''}"
         role="listitem" tabindex="0"
         data-id="${s.id}"
         data-name="${esc(s.name)}"
         data-desc="${esc(s.description || '')}"
         data-type="${s.skill_type}"
         data-unlock="${s.unlock_level}"
         data-cur="${s.current_level}"
         data-max="${s.max_level}"
         data-locked="${isLocked}"
         aria-label="${esc(s.name)} – ${isLocked ? 'locked' : s.current_level + '/' + s.max_level}">
      ${isLocked ? '<span class="skill-card__lock-icon">🔒</span>' : ''}
      <div class="skill-card__top">
        <span class="skill-card__icon">${icon}</span>
        <span class="skill-card__type-badge ${typeCls}">${s.skill_type}</span>
      </div>
      <div class="skill-card__name">${esc(s.name)}</div>
      <div class="skill-card__level">${isLocked ? `Requires Lv.${s.unlock_level}` : `${s.current_level} / ${s.max_level}`}</div>
      <div class="skill-card__bar">
        <div class="progress progress--sm">
          <div class="progress__fill ${isMaxed ? 'progress__fill--gold' : ''}" style="width:${pct}%"></div>
        </div>
      </div>
      ${canAlloc ? `<div class="skill-card__alloc"><button class="btn btn--primary btn--sm" style="width:100%" onclick="allocSkill(${s.id}, event)">＋ Upgrade</button></div>` : ''}
      ${canUnlock ? `<div class="skill-card__alloc"><button class="btn btn--accent btn--sm" style="width:100%" onclick="unlockSkill(${s.id}, event)">🔓 Unlock</button></div>` : ''}
      ${isMaxed ? '<div style="text-align:center;font-size:.78rem;color:var(--gold);font-weight:700;margin-top:.4rem">✦ MAX</div>' : ''}
    </div>`;
}

// ── Tooltip ─────────────────────────────────────────────────
function showTip(e) {
  const c   = e.currentTarget;
  const tip = document.getElementById('skillTooltip');
  const locked = c.dataset.locked === 'true';
  tip.innerHTML = `
    <strong style="color:var(--accent)">${c.dataset.name}</strong><br/>
    <em style="color:var(--muted);font-size:.78rem">${c.dataset.type} skill</em><br/>
    <span style="margin:.4rem 0;display:block">${c.dataset.desc || 'No description.'}</span>
    <span style="color:var(--muted);font-size:.78rem">
      ${locked ? `🔒 Requires level ${c.dataset.unlock}` : `Level ${c.dataset.cur}/${c.dataset.max}`}
    </span>`;
  tip.hidden = false;
  moveTip(e);
}
function moveTip(e) {
  const tip = document.getElementById('skillTooltip');
  const x   = Math.min(e.clientX + 14, window.innerWidth - 280);
  const y   = Math.min(e.clientY + 14, window.innerHeight - 120);
  tip.style.left = x + 'px';
  tip.style.top  = y + 'px';
}
function hideTip() { document.getElementById('skillTooltip').hidden = true; }

// ── Card click → show modal ──────────────────────────────────
function onCardClick(e) {
  if (e.target.closest('button')) return;
  const card = e.currentTarget;
  openSkillModal(parseInt(card.dataset.id));
}

function openSkillModal(skillId) {
  const s   = _skills.find(x => x.id === skillId);
  if (!s) return;
  const icon = { active: '⚡', passive: '🛡️' }[s.skill_type] || '✦';
  const canAlloc  = s.unlocked && s.current_level < s.max_level && _available > 0;
  const canUnlock = s.can_unlock && !s.unlocked;

  document.getElementById('skillModalContent').innerHTML = `
    <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:1rem">
      <span style="font-size:2.5rem">${icon}</span>
      <div>
        <h2 style="font-size:1.2rem;font-weight:800">${esc(s.name)}</h2>
        <span class="badge badge--${s.skill_type === 'active' ? 'submitted' : 'common'}">${s.skill_type}</span>
      </div>
    </div>
    <p style="color:var(--muted);margin-bottom:1rem;font-size:.9rem">${esc(s.description || 'No description.')}</p>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:.75rem;margin-bottom:1rem;font-size:.88rem">
      <div><span style="color:var(--muted)">Level:</span> <strong>${s.current_level} / ${s.max_level}</strong></div>
      <div><span style="color:var(--muted)">Unlock at:</span> <strong>Lv.${s.unlock_level}</strong></div>
      <div><span style="color:var(--muted)">Status:</span> <strong>${s.unlocked ? '✅ Unlocked' : '🔒 Locked'}</strong></div>
      <div><span style="color:var(--muted)">Type:</span> <strong>${s.skill_type}</strong></div>
    </div>
    <div class="progress" style="margin-bottom:1rem">
      <div class="progress__fill" style="width:${s.max_level ? Math.round(s.current_level/s.max_level*100) : 0}%"></div>
    </div>
    <div style="display:flex;gap:.75rem;flex-wrap:wrap">
      ${canAlloc  ? `<button class="btn btn--primary" onclick="allocSkill(${s.id})">＋ Upgrade Skill</button>` : ''}
      ${canUnlock ? `<button class="btn btn--accent"  onclick="unlockSkill(${s.id})">🔓 Unlock Skill</button>` : ''}
      <button class="btn btn--ghost" onclick="closeSkillModal()">Close</button>
    </div>`;
  document.getElementById('skillModal').hidden = false;
}

function closeSkillModal() { document.getElementById('skillModal').hidden = true; }
window.closeSkillModal = closeSkillModal;

// ── Allocate skill point ─────────────────────────────────────
async function allocSkill(skillId, event) {
  event?.stopPropagation();
  if (_available <= 0) { showToast('No skill points available', 'info'); return; }

  try {
    const res = await apiCall(`${API}/player/${PLAYER_ID}/skills/allocate`, {
      method: 'POST',
      body: JSON.stringify({ skill_id: skillId }),
    });
    showToast(`✅ Skill upgraded! (${res.new_level}/${_skills.find(s=>s.id===skillId)?.max_level})`, 'success');
    closeSkillModal();
    await loadSkills();
  } catch (e) {
    showToast(`❌ ${e.message}`, 'error');
  }
}
window.allocSkill = allocSkill;

// ── Unlock skill ─────────────────────────────────────────────
async function unlockSkill(skillId, event) {
  event?.stopPropagation();
  try {
    const res = await apiCall(`${API}/player/${PLAYER_ID}/skills/unlock`, {
      method: 'POST',
      body: JSON.stringify({ skill_id: skillId }),
    });
    showToast(`✅ Skill unlocked: ${_skills.find(s=>s.id===skillId)?.name}!`, 'success');
    closeSkillModal();
    await loadSkills();
  } catch (e) {
    showToast(`❌ ${e.message}`, 'error');
  }
}
window.unlockSkill = unlockSkill;

// ── Filter ───────────────────────────────────────────────────
function filterSkills() {
  _filterType = document.getElementById('filterType')?.value || 'all';
  renderSkills();
}
window.filterSkills = filterSkills;

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadSkills();
  document.getElementById('skillModal')?.addEventListener('click', e => {
    if (e.target.id === 'skillModal') closeSkillModal();
  });
});
