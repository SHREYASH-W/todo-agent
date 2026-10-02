/**
 * Career Hunter Module JavaScript – Requirements 15.1-21.7
 */
'use strict';
const API = '/api';
let _allJobs=[], _allApps=[], _pendingJobId=null;
function escHtml(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}

async function apiFetch(url,opts={}){
  const r=await fetch(url,{headers:{'Content-Type':'application/json'},...opts});
  if(!r.ok) throw new Error(r.status);
  return r.json();
}

// ── Load ─────────────────────────────────────────────────────
async function loadAll() {
  await Promise.all([loadJobs(), loadApps()]);
}

async function loadJobs() {
  const data = await apiFetch(`${API}/career/jobs?player_id=${PLAYER_ID}`);
  _allJobs = data.jobs||[];
  renderJobs(_allJobs);
}

async function loadApps() {
  const data = await apiFetch(`${API}/career/applications?player_id=${PLAYER_ID}`);
  _allApps = data.applications||[];
  const s = data.stats||{};
  document.getElementById('totalApps').textContent    = s.total||0;
  document.getElementById('responseRate').textContent  = (s.response_rate||0)+'%';
  document.getElementById('interviewRate').textContent = (s.interview_rate||0)+'%';
  document.getElementById('offerRate').textContent     = (s.offer_rate||0)+'%';
  renderApps(_allApps);
}

// ── Render Jobs ───────────────────────────────────────────────
function renderJobs(jobs) {
  const tbody = document.getElementById('jobsTbody');
  if(!tbody) return;
  if(!jobs.length){ tbody.innerHTML='<tr><td colspan="5" style="color:var(--clr-muted)">No jobs found. Try scraping!</td></tr>'; return; }
  tbody.innerHTML = jobs.map(j=>`
    <tr>
      <td>${escHtml(j.title)}</td>
      <td>${escHtml(j.company)}</td>
      <td>${escHtml(j.location)}</td>
      <td><span class="badge" style="background:rgba(108,99,255,.2);color:#fff">${j.match_score||0}%</span></td>
      <td><button class="btn btn--primary" style="font-size:.75rem;padding:.3rem .6rem" onclick="generateCL(${j.id},'${escHtml(j.title)}','${escHtml(j.company)}')">Apply</button></td>
    </tr>`).join('');
}

// ── Render Apps ───────────────────────────────────────────────
function renderApps(apps) {
  const tbody = document.getElementById('appsTbody');
  if(!tbody) return;
  if(!apps.length){ tbody.innerHTML='<tr><td colspan="5" style="color:var(--clr-muted)">No applications yet.</td></tr>'; return; }
  tbody.innerHTML = apps.map(a=>`
    <tr>
      <td>${escHtml(a.company||'—')}</td>
      <td>${escHtml(a.title||'—')}</td>
      <td><span class="badge badge--${a.status}">${escHtml(a.status)}</span></td>
      <td style="font-size:.8rem;color:var(--clr-muted)">${a.submitted_at?new Date(a.submitted_at).toLocaleDateString():''}</td>
      <td>
        <select onchange="updateStatus(${a.id},this.value)" style="background:var(--clr-surface);border:1px solid var(--clr-border);color:var(--clr-text);border-radius:4px;font-size:.8rem;padding:.2rem" aria-label="Update status">
          <option>Update…</option>
          <option value="under_review">Under Review</option>
          <option value="interview">Interview</option>
          <option value="offered">Offered</option>
          <option value="rejected">Rejected</option>
        </select>
      </td>
    </tr>`).join('');
}

// ── Scrape ────────────────────────────────────────────────────
async function triggerScrape() {
  const btn = document.getElementById('scrapeBtn');
  const status = document.getElementById('scrapeStatus');
  btn.disabled = true;
  status.textContent = '⏳ Scraping…';
  try {
    const data = await apiFetch(`${API}/career/scrape`,{method:'POST',body:JSON.stringify({player_id:PLAYER_ID})});
    status.textContent = `✓ Found ${data.jobs_found} jobs`;
    await loadJobs();
  } catch(e) {
    status.textContent = '✗ Scrape failed';
  } finally {
    btn.disabled = false;
  }
}
window.triggerScrape = triggerScrape;

// ── Cover Letter ──────────────────────────────────────────────
async function generateCL(jobId, title, company) {
  _pendingJobId = jobId;
  document.getElementById('clText').value = '⏳ Generating cover letter…';
  document.getElementById('clModal').hidden = false;
  try {
    const data = await apiFetch(`${API}/career/cover-letter`,{
      method:'POST',
      body:JSON.stringify({job_description:`${title} at ${company}`,resume:'',job_title:title,company})
    });
    document.getElementById('clText').value = data.cover_letter||'Cover letter generation failed.';
  } catch(e) {
    document.getElementById('clText').value = 'AI service unavailable. Please write your cover letter manually.';
  }
}
window.generateCL = generateCL;

async function submitApplication() {
  if(!_pendingJobId) return;
  const cl = document.getElementById('clText').value;
  try {
    await apiFetch(`${API}/career/applications`,{
      method:'POST',
      body:JSON.stringify({player_id:PLAYER_ID,job_id:_pendingJobId,cover_letter:cl})
    });
    closeCL();
    loadApps();
  } catch(e) { alert('Failed to submit application.'); }
}
window.submitApplication = submitApplication;

function closeCL() { document.getElementById('clModal').hidden=true; _pendingJobId=null; }
window.closeCL = closeCL;

// ── Filters ───────────────────────────────────────────────────
function filterJobs(minScore) {
  document.getElementById('scoreLabel').textContent = `Min score: ${minScore}`;
  renderJobs(_allJobs.filter(j=>(j.match_score||0)>=parseInt(minScore)));
}
function filterApps(status) {
  renderApps(status ? _allApps.filter(a=>a.status===status) : _allApps);
}
async function updateStatus(appId, status) {
  if(status==='Update…') return;
  try {
    await apiFetch(`${API}/career/applications/${appId}`,{method:'PUT',body:JSON.stringify({status,player_id:PLAYER_ID})});
    loadApps();
  } catch(e){ console.error('Status update:',e); }
}
window.filterJobs  = filterJobs;
window.filterApps  = filterApps;
window.updateStatus = updateStatus;

document.addEventListener('DOMContentLoaded', loadAll);
