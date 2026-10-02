/**
 * Analytics JavaScript – Requirements 27.1-27.7 (Chart.js)
 */
'use strict';
let _xpChart, _questChart, _statChart, _currentDays = 7;

const CHART_DEFAULTS = {
  color: '#e0e0f0',
  gridColor: 'rgba(255,255,255,.08)',
  primary: '#6c63ff',
  accent:  '#00d4ff',
  gold:    '#ffd700',
  success: '#00cc66',
  danger:  '#ff4444',
};

function getChartOptions(type) {
  const base = { responsive:true, maintainAspectRatio:true,
    plugins:{ legend:{ labels:{ color:CHART_DEFAULTS.color } } } };
  if(type==='radar') return { ...base, scales:{ r:{
    grid:{ color:CHART_DEFAULTS.gridColor },
    pointLabels:{ color:CHART_DEFAULTS.color },
    ticks:{ color:CHART_DEFAULTS.color, backdropColor:'transparent' }
  }}};
  return { ...base, scales:{
    x:{ ticks:{ color:CHART_DEFAULTS.color }, grid:{ color:CHART_DEFAULTS.gridColor } },
    y:{ ticks:{ color:CHART_DEFAULTS.color }, grid:{ color:CHART_DEFAULTS.gridColor }, beginAtZero:true }
  }};
}

// ── Mock data generator (replace with real API calls) ───────
function generateMockData(days) {
  const labels = [];
  const xpData = [];
  const now = new Date();
  const count = days||30;
  for(let i=count-1; i>=0; i--) {
    const d = new Date(now); d.setDate(d.getDate()-i);
    labels.push(d.toLocaleDateString('en',{month:'short',day:'numeric'}));
    xpData.push(Math.floor(Math.random()*200+50));
  }
  return { labels, xpData };
}

// ── Build / Update Charts ─────────────────────────────────
async function loadAnalytics(days) {
  _currentDays = days;
  try {
    const p = await (await fetch(`/api/player/${PLAYER_ID}/stats`)).json();
    updateKPIs(p);
    buildXpChart(days);
    buildQuestChart();
    buildStatChart(p);
  } catch(e) { console.error('Analytics load:', e); }
}

function updateKPIs(p) {
  document.getElementById('kpiStreak').textContent = p.daily_streak||'0';
  document.getElementById('kpiTotal').textContent  = p.total_quests_completed||'0';
  document.getElementById('kpiXpDay').textContent  = p.avg_xp_per_day||'0';
}

function buildXpChart(days) {
  const { labels, xpData } = generateMockData(days||7);
  const ctx = document.getElementById('xpChart');
  if(!ctx) return;
  if(_xpChart) _xpChart.destroy();
  _xpChart = new Chart(ctx, {
    type:'line',
    data:{ labels, datasets:[{ label:'XP Gained', data:xpData,
      borderColor:CHART_DEFAULTS.primary, backgroundColor:'rgba(108,99,255,.1)',
      tension:.4, fill:true, pointRadius:3 }] },
    options: getChartOptions('line')
  });
}

function buildQuestChart() {
  const ctx = document.getElementById('questChart');
  if(!ctx) return;
  if(_questChart) _questChart.destroy();
  _questChart = new Chart(ctx, {
    type:'bar',
    data:{ labels:['Daily','Main','Instant','Emergency'],
      datasets:[{ label:'Completed', data:[45,12,8,3],
        backgroundColor:[CHART_DEFAULTS.primary,CHART_DEFAULTS.accent,CHART_DEFAULTS.gold,CHART_DEFAULTS.danger] }] },
    options: getChartOptions('bar')
  });
}

function buildStatChart(p) {
  const ctx = document.getElementById('statChart');
  if(!ctx) return;
  if(_statChart) _statChart.destroy();
  _statChart = new Chart(ctx, {
    type:'radar',
    data:{ labels:['STR','INT','AGI','VIT','SEN','LUK'],
      datasets:[{ label:'Stats', data:[p.str_stat,p.int_stat,p.agi_stat,p.vit_stat,p.sen_stat,p.luk_stat]||[10,10,10,10,10,10],
        borderColor:CHART_DEFAULTS.accent, backgroundColor:'rgba(0,212,255,.1)', pointBackgroundColor:CHART_DEFAULTS.accent }] },
    options: getChartOptions('radar')
  });
}

document.addEventListener('DOMContentLoaded', () => {
  loadAnalytics(7);
  document.querySelectorAll('.range-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.range-btn').forEach(b=>b.classList.remove('range-btn--active'));
      btn.classList.add('range-btn--active');
      loadAnalytics(parseInt(btn.dataset.days));
    });
  });
});
