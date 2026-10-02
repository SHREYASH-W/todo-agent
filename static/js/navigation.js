/**
 * Navigation JavaScript – Requirements 26.1-26.7, Notification requirements
 * Handles notification polling and dropdown.
 */
'use strict';

const NOTIFY_POLL_MS = 30_000;
let _notifyTimer;

function elById(id) { return document.getElementById(id); }

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Notification Dropdown ────────────────────────────────────
function initNotifications() {
  const btn      = elById('notifyBtn');
  const dropdown = elById('notifyDropdown');
  if (!btn || !dropdown) return;

  btn.addEventListener('click', () => {
    const open = dropdown.hidden === false;
    dropdown.hidden = open;
    btn.setAttribute('aria-expanded', String(!open));
  });

  // Close on outside click
  document.addEventListener('click', e => {
    if (!btn.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.hidden = true;
      btn.setAttribute('aria-expanded', 'false');
    }
  });

  pollNotifications();
  _notifyTimer = setInterval(pollNotifications, NOTIFY_POLL_MS);
}

async function pollNotifications() {
  const playerId = window.PLAYER_ID;
  if (!playerId) return;
  try {
    const res  = await fetch(`/api/player/${playerId}/notifications`);
    if (!res.ok) return;
    const data = await res.json();
    renderNotifications(data.notifications || []);
  } catch (_) {}
}

function renderNotifications(notifications) {
  const badge = elById('notifyBadge');
  const list  = elById('notifyList');
  const empty = document.querySelector('.nav__notify-empty');

  const unread = notifications.filter(n => !n.is_read);

  if (badge) {
    badge.hidden = unread.length === 0;
    badge.textContent = unread.length;
  }

  if (!list) return;

  if (!notifications.length) {
    list.innerHTML = '';
    if (empty) empty.style.display = 'block';
    return;
  }

  if (empty) empty.style.display = 'none';
  list.innerHTML = notifications.slice(0, 10).map(n => `
    <li class="nav__notify-item ${n.is_read ? '' : 'nav__notify-item--unread'}">
      <strong>${escHtml(n.title)}</strong><br/>
      <span>${escHtml(n.message)}</span>
    </li>`).join('');
}

document.addEventListener('DOMContentLoaded', initNotifications);
