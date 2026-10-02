/**
 * Career Hunter Module – fully functional
 * Scrape jobs, match, apply, cover letter AI, status updates
 */
'use strict';

const API = '/api';
let _jobs = [];
let _currentJobId = null;

async function req(url, opts = {}) {
  const r = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.error || `HTTP ${r.status}`); }
  return r.json();
}

// ── Init ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadJobs();
  loadApplications();
  loadStats();

  // Close modals on overlay click
  document.getElementById('clModal')?.addEventListener('click', e => { if (e.target.id==='clModal') closeClModal(); });
  document.getElementById('statusModal')?.addEventListener('click', e => { if (e.target.id==='statusModal') closeStatusModal(); });
});

// ── Stats ────────────────────────────────────────────────────
async function loadStats() {
  try {
    const data = await req(`${API}/career/applications?player_id=${PLAYER_ID}`);
    const stats = data.stats || {};
    const apps  = data.applications || [];

    document.getElementById('statApps').textContent  = apps.length || '0';
    document.getElementById('statResp').textContent  = stats.response_rate  ? `${stats.response_rate}%`  : '—';
    document.getElementById('statIntv').textContent  = stats.interview_rate ? `${stats.interview_rate}%` : '—';
    document.getElementById('statOffer').textContent = stats.offer_rate     ? `${stats.offer_rate}%`     : '—';
  } catch (_) {}
}

// ── Jobs ─────────────────────────────────────────────────────
async function loadJobs() {
  try {
    const data = await req(`${API}/career/jobs?player_id=${PLAYER_ID}`);
    _jobs = data.jobs || [];
    renderJobs();
  } catch (e) {
    document.getElementById('jobsTbody').innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:1.5rem">Failed to load jobs. Try scraping first.</td></tr>`;
  }
}

function renderJobs() {
  const tbody    = document.getElementById('jobsTbody');
  const minScore = parseInt(document.getElementById('scoreFilter')?.value || 0);
  const filtered = _jobs.filter(j => (j.match_score || 0) >= minScore);
  const countEl  = document.getElementById('jobCount');
  if (countEl) countEl.textContent = `${filtered.length} jobs`;

  if (!filtered.length) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:2rem">
      ${_jobs.length ? 'No jobs match the current score filter.' : 'No matched jobs yet. Click "Find Jobs" to scrape.'}
    </td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(j => {
    const score = j.match_score || 0;
    const cls   = score >= 70 ? 'match-score--high' : score >= 40 ? 'match-score--mid' : 'match-score--low';
    return `<tr>
      <td style="font-weight:600">${esc(j.title)}</td>
      <td>${esc(j.company)}</td>
      <td style="color:var(--muted)">${esc(j.location || '—')}</td>
      <td>
        <div class="progress progress--sm match-bar" style="margin-bottom:.3rem">
          <div class="progress__fill" style="width:${score}%;background:${score>=70?'var(--success)':score>=40?'var(--warn)':'var(--muted)'}"></div>
        </div>
        <span class="match-score ${cls}">${score}%</span>
      </td>
      <td>
        ${j.url ? `<a href="${esc(j.url)}" target="_blank" rel="noopener" class="btn btn--ghost btn--sm" style="margin-bottom:.25rem">🔗 View</a> ` : ''}
        <button class="btn btn--primary btn--sm" onclick="openApplyModal(${j.id})">Apply</button>
      </td>
    </tr>`;
  }).join('');
}
window.renderJobs = renderJobs;

// ── Scrape ───────────────────────────────────────────────────
async function triggerScrape() {
  const btn    = document.getElementById('scrapeBtn');
  const status = document.getElementById('scrapeStatus');
  const kw     = document.getElementById('scrapeKeywords')?.value || 'Software Engineer';
  const loc    = document.getElementById('scrapeLocation')?.value || '';

  btn.disabled = true; btn.textContent = '🔍 Searching…';
  if (status) status.textContent = 'Searching for jobs…';

  try {
    const res = await req(`${API}/career/scrape`, {
      method: 'POST',
      body: JSON.stringify({ keywords: [kw], location: loc, sources: ['linkedin','indeed'] }),
    });
    if (status) status.textContent = `✅ Found ${res.jobs_found || 0} jobs. Loading matches…`;
    showToast(`Found ${res.jobs_found || 0} jobs!`, 'success');
    await loadJobs();
    await loadStats();
  } catch (e) {
    if (status) status.textContent = `⚠️ ${e.message}`;
    showToast(`Scrape error: ${e.message}`, 'error');
  } finally {
    btn.disabled = false; btn.textContent = '🔍 Find Jobs';
  }
}
window.triggerScrape = triggerScrape;

// ── Applications ─────────────────────────────────────────────
async function loadApplications() {
  const statusFilter = document.getElementById('appStatusFilter')?.value || '';
  const url = `${API}/career/applications?player_id=${PLAYER_ID}${statusFilter ? '&status='+statusFilter : ''}`;
  const tbody = document.getElementById('appsTbody');

  try {
    const data = await req(url);
    const apps = data.applications || [];

    if (!apps.length) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:2rem">No applications yet. Apply to jobs above!</td></tr>`;
      return;
    }

    tbody.innerHTML = apps.map(a => {
      // Find job info from cached jobs
      const job = _jobs.find(j => j.id === a.job_id);
      const company = job?.company || `Job #${a.job_id}`;
      const title   = job?.title   || '—';
      const date    = a.submitted_at ? new Date(a.submitted_at).toLocaleDateString() : '—';

      return `<tr>
        <td style="font-weight:600">${esc(company)}</td>
        <td>${esc(title)}</td>
        <td><span class="badge badge--${a.status}">${a.status.replace('_',' ')}</span></td>
        <td style="color:var(--muted);font-size:.85rem">${date}</td>
        <td>
          <button class="btn btn--ghost btn--sm" onclick="openStatusModal(${a.id}, '${a.status}')">Update</button>
        </td>
      </tr>`;
    }).join('');
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--muted)">Failed to load</td></tr>`;
  }
}
window.loadApplications = loadApplications;

// ── Apply Modal ──────────────────────────────────────────────
function openApplyModal(jobId) {
  _currentJobId = jobId;
  const job = _jobs.find(j => j.id === jobId);
  document.getElementById('clModalTitle').textContent = `Apply – ${job?.title || 'Job'}`;
  document.getElementById('clJobInfo').innerHTML = job
    ? `<strong>${esc(job.title)}</strong> at <strong>${esc(job.company)}</strong><br/><span style="color:var(--muted)">${esc(job.location||'')}${job.match_score?` · Match: ${job.match_score}%`:''}</span>`
    : '';
  document.getElementById('clText').value   = '';
  document.getElementById('clResume').value = '';
  document.getElementById('clModal').hidden = false;
}
window.openApplyModal = openApplyModal;

function closeClModal() {
  document.getElementById('clModal').hidden = true;
  _currentJobId = null;
}
window.closeClModal = closeClModal;

async function generateCoverLetter() {
  const btn = document.getElementById('genClBtn');
  const job = _jobs.find(j => j.id === _currentJobId);
  if (!job) { showToast('No job selected', 'error'); return; }

  btn.disabled = true; btn.textContent = '✨ Generating…';
  document.getElementById('clText').value = 'Generating cover letter with AI…';

  try {
    const res = await req(`${API}/career/cover-letter`, {
      method: 'POST',
      body: JSON.stringify({
        job_description: `${job.title} at ${job.company}. ${job.description || ''}`,
        resume: document.getElementById('clResume').value || '',
        job_title: job.title,
        company:   job.company,
      }),
    });
    document.getElementById('clText').value = res.cover_letter || '';
    showToast('✅ Cover letter generated!', 'success');
  } catch (e) {
    document.getElementById('clText').value = '';
    showToast(`AI unavailable: ${e.message}`, 'error');
  } finally {
    btn.disabled = false; btn.textContent = '✨ Generate with AI';
  }
}
window.generateCoverLetter = generateCoverLetter;

async function submitApplication() {
  if (!_currentJobId) return;
  const btn = document.getElementById('submitAppBtn');
  btn.disabled = true; btn.textContent = 'Submitting…';

  try {
    await req(`${API}/career/applications`, {
      method: 'POST',
      body: JSON.stringify({
        player_id:    PLAYER_ID,
        job_id:       _currentJobId,
        cover_letter: document.getElementById('clText').value || '',
      }),
    });
    showToast('📨 Application submitted! +50 XP', 'success');
    closeClModal();
    await loadApplications();
    await loadStats();
  } catch (e) {
    showToast(`❌ ${e.message}`, 'error');
  } finally {
    btn.disabled = false; btn.textContent = '📨 Submit Application';
  }
}
window.submitApplication = submitApplication;

// ── Status Update Modal ──────────────────────────────────────
function openStatusModal(appId, currentStatus) {
  document.getElementById('statusAppId').value = appId;
  document.getElementById('statusNotes').value = '';
  // Set current status as default
  const sel = document.getElementById('newStatus');
  if (sel) {
    const next = { submitted:'under_review', under_review:'interview_scheduled', interview_scheduled:'offered' }[currentStatus] || 'under_review';
    sel.value = next;
  }
  document.getElementById('statusModal').hidden = false;
}
window.openStatusModal = openStatusModal;

function closeStatusModal() { document.getElementById('statusModal').hidden = true; }
window.closeStatusModal = closeStatusModal;

async function confirmStatusUpdate() {
  const appId  = document.getElementById('statusAppId').value;
  const status = document.getElementById('newStatus').value;
  const notes  = document.getElementById('statusNotes').value;
  const btn    = document.querySelector('#statusModal .btn--primary');

  if (!appId) return;
  btn.disabled = true; btn.textContent = 'Updating…';

  try {
    await req(`${API}/career/applications/${appId}`, {
      method: 'PUT',
      body: JSON.stringify({ player_id: PLAYER_ID, status, notes }),
    });
    showToast(`✅ Status updated to "${status.replace('_',' ')}"`, 'success');
    closeStatusModal();
    await loadApplications();
    await loadStats();
  } catch (e) {
    showToast(`❌ ${e.message}`, 'error');
  } finally {
    btn.disabled = false; btn.textContent = 'Update';
  }
}
window.confirmStatusUpdate = confirmStatusUpdate;
