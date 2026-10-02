/**
 * Analytics – real API data, Chart.js visualisations
 */
'use strict';

let _xpChart, _questChart, _statChart;
const C = {
  text: '#e4e4f4', grid: 'rgba(255,255,255,.07)',
  primary: '#6c63ff', accent: '#00d4ff', gold: '#ffd700',
  success: '#00cc66', danger: '#ff4466', warn: '#ff8800',
};

function chartOpts(type) {
  const base = {
    responsive: true, maintainAspectRatio: false,
    animation: { duration: 500 },
    plugins: { legend: { labels: { color: C.text, font: { size: 12 } } } },
  };
  if (type === 'radar') return {
    ...base,
    scales: { r: {
      grid: { color: C.grid },
      pointLabels: { color: C.text, font: { size: 12, weight: '600' } },
      ticks: { color: C.text, backdropColor: 'transparent', stepSize: 5 },
      min: 0,
    }},
  };
  return {
    ...base,
    scales: {
      x: { ticks: { color: C.text, font: { size: 11 } }, grid: { color: C.grid } },
      y: { ticks: { color: C.text, font: { size: 11 } }, grid: { color: C.grid }, beginAtZero: true },
    },
  };
}

async function loadAnalytics(days = 7) {
  try {
    const data = await (await fetch(`/api/player/${PLAYER_ID}/analytics?days=${days}`)).json();

    // KPIs
    const k = data.kpis || {};
    document.getElementById('kpiStreak').textContent = k.daily_streak ?? '0';
    document.getElementById('kpiTotal').textContent  = k.total_quests_completed ?? '0';
    document.getElementById('kpiXpDay').textContent  = k.avg_xp_per_day ?? '0';
    document.getElementById('kpiLevel').textContent  = `Lv.${k.level ?? 1} ${k.rank ?? 'E'}`;

    buildXpChart(data.xp_over_time || { labels: [], data: [] });
    buildQuestChart(data.quests_by_type || {});
    buildStatChart(data.stats || {});
  } catch (e) {
    console.error('Analytics error:', e);
    showToast('Failed to load analytics', 'error');
  }
}

function buildXpChart(xp) {
  const ctx = document.getElementById('xpChart');
  if (!ctx) return;
  if (_xpChart) _xpChart.destroy();

  // Shorten date labels
  const labels = (xp.labels || []).map(d => {
    const dt = new Date(d);
    return dt.toLocaleDateString('en', { month: 'short', day: 'numeric' });
  });

  _xpChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'XP Gained',
        data: xp.data || [],
        borderColor: C.primary,
        backgroundColor: 'rgba(108,99,255,.1)',
        tension: .35, fill: true, pointRadius: 3,
        pointBackgroundColor: C.primary,
      }],
    },
    options: chartOpts('line'),
  });
}

function buildQuestChart(byType) {
  const ctx = document.getElementById('questChart');
  if (!ctx) return;
  if (_questChart) _questChart.destroy();

  const vals = [byType.daily||0, byType.main||0, byType.instant||0, byType.emergency||0];
  const total = vals.reduce((a,b) => a+b, 0);

  // Use doughnut if all values 0, otherwise bar
  if (total === 0) {
    _questChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Daily', 'Main', 'Instant', 'Emergency'],
        datasets: [{ data: [1,1,1,1], backgroundColor: [C.primary, C.accent, C.gold, C.danger], borderWidth: 0 }],
      },
      options: { ...chartOpts('doughnut'), plugins: { legend: { labels: { color: C.text } } } },
    });
  } else {
    _questChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Daily', 'Main', 'Instant', 'Emergency'],
        datasets: [{
          label: 'Completed',
          data: vals,
          backgroundColor: [
            'rgba(108,99,255,.75)', 'rgba(0,212,255,.75)',
            'rgba(255,215,0,.75)',  'rgba(255,68,102,.75)',
          ],
          borderRadius: 6, borderSkipped: false,
        }],
      },
      options: chartOpts('bar'),
    });
  }
}

function buildStatChart(stats) {
  const ctx = document.getElementById('statChart');
  if (!ctx) return;
  if (_statChart) _statChart.destroy();

  _statChart = new Chart(ctx, {
    type: 'radar',
    data: {
      labels: ['STR', 'INT', 'AGI', 'VIT', 'SEN', 'LUK'],
      datasets: [{
        label: 'Current Stats',
        data: [
          stats.str_stat||10, stats.int_stat||10, stats.agi_stat||10,
          stats.vit_stat||10, stats.sen_stat||10, stats.luk_stat||10,
        ],
        borderColor: C.accent,
        backgroundColor: 'rgba(0,212,255,.1)',
        pointBackgroundColor: C.accent,
        pointBorderColor: '#fff',
        pointRadius: 5,
        borderWidth: 2,
      }],
    },
    options: chartOpts('radar'),
  });
}

document.addEventListener('DOMContentLoaded', () => {
  loadAnalytics(7);

  document.querySelectorAll('.range-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.range-btn').forEach(b => {
        b.classList.remove('range-btn--active');
        b.classList.add('btn--ghost'); b.classList.remove('btn--primary');
      });
      btn.classList.add('range-btn--active', 'btn--primary');
      btn.classList.remove('btn--ghost');
      loadAnalytics(parseInt(btn.dataset.days) || 7);
    });
  });
});
