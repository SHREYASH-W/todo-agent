/**
 * Skill Tree JavaScript – Requirements 24.1-24.7
 */
'use strict';
const API = '/api';
function escHtml(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
const SKILL_ICONS = {active:'⚡',passive:'🛡️'};

async function apiFetch(url, opts={}) {
  const r = await fetch(url,{headers:{'Content-Type':'application/json'},...opts});
  if(!r.ok) throw new Error(r.status);
  return r.json();
}

async function loadSkills() {
  const data = await apiFetch(`${API}/player/${PLAYER_ID}/skills`);
  document.getElementById('skillPointsBadge').textContent = `${data.skill_points_available} point${data.skill_points_available!==1?'s':''}`;
  renderSkillTree(data.skills||[], data.skill_points_available);
}

function renderSkillTree(skills, availablePoints) {
  const tree = document.getElementById('skillTree');
  tree.innerHTML = skills.map(s => {
    const locked   = !s.unlocked ? 'skill-card--locked' : 'skill-card--unlocked';
    const canAlloc = s.unlocked && s.current_level < s.max_level && availablePoints > 0;
    return `
      <div class="skill-card ${locked}" role="listitem"
           data-skill-id="${s.id}"
           data-name="${escHtml(s.name)}"
           data-desc="${escHtml(s.description)}"
           data-type="${s.skill_type}"
           data-unlock="${s.unlock_level}"
           data-cur="${s.current_level}"
           data-max="${s.max_level}"
           tabindex="0"
           aria-label="${escHtml(s.name)} – ${s.unlocked?'unlocked':'locked'}">
        <div class="skill-card__icon">${SKILL_ICONS[s.skill_type]||'✦'}</div>
        <div class="skill-card__name">${escHtml(s.name)}</div>
        <div class="skill-card__level">${s.current_level}/${s.max_level}</div>
        <div class="skill-card__type">${s.skill_type}</div>
        ${canAlloc ? `<div class="skill-card__btn"><button class="btn btn--primary" style="font-size:.75rem;padding:.3rem .7rem" onclick="allocSkill(${s.id},event)">+1</button></div>` : ''}
      </div>`;
  }).join('');

  // Tooltip events
  tree.querySelectorAll('.skill-card').forEach(card => {
    card.addEventListener('mouseenter', showTooltip);
    card.addEventListener('mousemove',  moveTooltip);
    card.addEventListener('mouseleave', hideTooltip);
    card.addEventListener('focus',      showTooltip);
    card.addEventListener('blur',       hideTooltip);
  });
}

function showTooltip(e) {
  const c = e.currentTarget;
  const tip = document.getElementById('skillTooltip');
  tip.innerHTML = `<strong>${escHtml(c.dataset.name)}</strong>
    <br/><em>${c.dataset.type}</em>
    <br/>${escHtml(c.dataset.desc)}
    <br/><span style="color:var(--clr-muted)">Unlock at level ${c.dataset.unlock} · ${c.dataset.cur}/${c.dataset.max}</span>`;
  tip.hidden = false;
  moveTooltip(e);
}
function moveTooltip(e) {
  const tip = document.getElementById('skillTooltip');
  tip.style.left = (e.clientX+14)+'px';
  tip.style.top  = (e.clientY+14)+'px';
}
function hideTooltip() { document.getElementById('skillTooltip').hidden = true; }

async function allocSkill(skillId, event) {
  event.stopPropagation();
  try {
    await apiFetch(`${API}/player/${PLAYER_ID}/skills/allocate`,{method:'POST',body:JSON.stringify({skill_id:skillId})});
    loadSkills();
  } catch(e) { console.error('Skill alloc:',e); }
}
window.allocSkill = allocSkill;

document.addEventListener('DOMContentLoaded', loadSkills);
