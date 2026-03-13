async function loadMeta() {
  try {
    const [summaryRes, updatedRes] = await Promise.all([
      fetch('/api/data_summary'),
      fetch('/api/last_updated'),
    ]);
    const summary = await summaryRes.json();
    const updated = await updatedRes.json();

    const incidentCount = summary.total_incidents ?? summary.total_records ?? '—';
    const cityCount = summary.unique_locations ?? summary.unique_cities ?? '—';

    const i = document.getElementById('metaIncidents');
    const c = document.getElementById('metaCities');
    const u = document.getElementById('metaUpdated');
    if (i) i.textContent = incidentCount;
    if (c) c.textContent = cityCount;
    if (u) u.textContent = updated.display || updated.time_str || updated.timestamp || 'Unknown';
  } catch (_) {}
}

async function checkRisk() {
  const cityInput = document.getElementById('cityInput');
  const output = document.getElementById('riskResult');
  const city = cityInput.value.trim();
  if (!city) return;

  output.classList.remove('show');
  try {
    const res = await fetch('/api/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ city }),
    });
    const data = await res.json();
    if (data.error) {
      document.getElementById('riskLevel').textContent = 'No result';
      document.getElementById('riskScore').textContent = data.error;
      document.getElementById('riskResolved').textContent = '';
      document.getElementById('riskConfidence').textContent = '';
      document.getElementById('riskDrivers').innerHTML = '';
      document.getElementById('riskBreakdown').innerHTML = '';
      document.getElementById('statTotal').textContent = '—';
      document.getElementById('statForce').textContent = '—';
      document.getElementById('statSensitive').textContent = '—';
      output.classList.add('show');
      return;
    }

    document.getElementById('riskLevel').textContent = data.risk_level || 'Unknown';
    document.getElementById('riskScore').textContent = `Risk score: ${data.risk_score ?? '—'} / 100`;
    document.getElementById('riskResolved').textContent = (data.query_input && data.resolved_location && data.query_input !== data.resolved_location)
      ? `Resolved: ${data.query_input} → ${data.resolved_location}`
      : '';
    document.getElementById('riskConfidence').textContent = data.confidence_reason || data.confidence || '';

    document.getElementById('statTotal').textContent = data.total_incidents ?? '—';
    document.getElementById('statForce').textContent = `${data.use_of_force ?? 0} (${data.use_of_force_pct ?? 0}%)`;
    document.getElementById('statSensitive').textContent = `${data.sensitive_locations ?? 0} (${data.sensitive_locations_pct ?? 0}%)`;

    const drivers = data.top_drivers || data.risk_drivers || data.drivers || [];
    document.getElementById('riskDrivers').innerHTML = drivers.slice(0, 4).map(d => {
      if (typeof d === 'string') return `<li>${d}</li>`;
      return `<li>${d.name}${typeof d.score !== 'undefined' ? ` — ${d.score}` : ''}</li>`;
    }).join('');

    const components = data.score_breakdown?.components || [];
    document.getElementById('riskBreakdown').innerHTML = components.map(c => {
      const score = typeof c.capped_score !== 'undefined' ? c.capped_score : c.raw_score;
      return `<li>${c.name}: ${c.count} × ${c.weight} = ${score}</li>`;
    }).join('');

    output.classList.add('show');
  } catch (e) {
    document.getElementById('riskLevel').textContent = 'Error';
    document.getElementById('riskScore').textContent = 'Could not fetch risk data.';
    document.getElementById('riskResolved').textContent = '';
    document.getElementById('riskConfidence').textContent = '';
    document.getElementById('riskDrivers').innerHTML = '';
    document.getElementById('riskBreakdown').innerHTML = '';
    output.classList.add('show');
  }
}

async function cityAutocomplete(query) {
  if (!query || query.length < 2) return [];
  const res = await fetch(`/api/cities?q=${encodeURIComponent(query)}`);
  return await res.json();
}

async function zipToCitySuggestion(query) {
  if (!/^\d{5}$/.test(query)) return [];
  try {
    const res = await fetch(`https://api.zippopotam.us/us/${query}`);
    if (!res.ok) return [];
    const data = await res.json();
    const place = (data.places || [])[0];
    if (!place) return [];
    const city = `${place['place name']}, ${place['state abbreviation']}`;
    return [city];
  } catch (_) {
    return [];
  }
}

function setupAutocomplete() {
  const input = document.getElementById('cityInput');
  const box = document.getElementById('autocomplete');
  if (!input || !box) return;

  input.addEventListener('input', async () => {
    const q = input.value.trim();
    if (q.length < 2) {
      box.style.display = 'none';
      return;
    }
    const [cities, zipSuggestion] = await Promise.all([
      cityAutocomplete(q),
      zipToCitySuggestion(q),
    ]);
    const combined = [...zipSuggestion, ...cities.filter(c => !zipSuggestion.includes(c))];
    if (!combined.length) {
      box.style.display = 'none';
      return;
    }
    box.innerHTML = combined.slice(0, 10).map(city => `<div class="autocomplete-item" data-city="${city}">${city}</div>`).join('');
    box.style.display = 'block';
  });

  box.addEventListener('click', (e) => {
    const item = e.target.closest('.autocomplete-item');
    if (!item) return;
    input.value = item.dataset.city;
    box.style.display = 'none';
  });

  document.addEventListener('click', (e) => {
    if (!box.contains(e.target) && e.target !== input) box.style.display = 'none';
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      checkRisk();
    }
  });
}

let mapStates = [];
let mapMeta = {};
let mapMetric = 'count';

function renderMoverBadges(movers) {
  const container = document.getElementById('stateMoverBadges');
  if (!container) return;
  if (!movers || !movers.length) {
    container.innerHTML = '<span class="muted">No recent trend spikes detected.</span>';
    return;
  }

  container.innerHTML = movers.slice(0, 5).map(item => {
    const delta = Number(item.delta30 || 0);
    const cls = delta > 0 ? 'badge up' : (delta < 0 ? 'badge down' : 'badge flat');
    const sign = delta > 0 ? '+' : '';
    return `<span class="${cls}">${item.state} ${sign}${delta}</span>`;
  }).join('');
}

async function loadStateCities(state) {
  const list = document.getElementById('stateCityList');
  const note = document.getElementById('stateQuickNote');
  if (!list) return;

  list.innerHTML = '<li class="muted">Loading cities…</li>';
  try {
    const res = await fetch(`/api/state-cities?state=${encodeURIComponent(state)}`);
    const payload = await res.json();
    const cities = payload.cities || [];

    if (note) {
      note.textContent = `${state} selected. Quick picks are the highest-volume cities in this dataset.`;
    }

    if (!cities.length) {
      list.innerHTML = `<li class="muted">No city suggestions available for ${state} yet.</li>`;
      return;
    }

    list.innerHTML = cities.map(item => (
      `<li><button type="button" class="city-jump" data-city="${item.location}">${item.location}</button> <span class="muted">(${item.incidents})</span></li>`
    )).join('');

    list.querySelectorAll('.city-jump').forEach(btn => {
      btn.addEventListener('click', () => {
        const input = document.getElementById('cityInput');
        if (!input) return;
        input.value = btn.dataset.city || '';
        checkRisk();
        input.scrollIntoView({ behavior: 'smooth', block: 'center' });
      });
    });
  } catch (_) {
    list.innerHTML = `<li class="muted">Could not load city suggestions for ${state}.</li>`;
  }
}

async function drawMap() {
  const chart = document.getElementById('usMapChart');
  const summary = document.getElementById('mapSummary');
  if (!chart || typeof Plotly === 'undefined' || !mapStates.length) return;

  const isRecent = mapMetric === 'recent30';
  const values = mapStates.map(s => isRecent ? (s.recent30 ?? 0) : (s.count ?? 0));
  const label = isRecent ? 'Recent 30d incidents' : 'All-time incidents';

  await Plotly.newPlot(chart, [{
    type: 'choropleth',
    locationmode: 'USA-states',
    locations: mapStates.map(s => s.state),
    z: values,
    text: mapStates.map(s => `${s.state}: ${isRecent ? (s.recent30 ?? 0) : (s.count ?? 0)} incidents`),
    colorscale: [
      [0, '#11273a'],
      [0.35, '#1d5c74'],
      [0.7, '#20b98e'],
      [1, '#7fffd4']
    ],
    marker: { line: { color: '#0b1219', width: 0.8 } },
    colorbar: { title: label, color: '#95a8be' },
    hovertemplate: '%{text}<extra></extra>'
  }], {
    geo: {
      scope: 'usa',
      bgcolor: 'rgba(0,0,0,0)',
      lakecolor: 'rgba(0,0,0,0)',
      showlakes: false,
      showcountries: false,
      subunitcolor: '#223345'
    },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { t: 0, r: 0, b: 0, l: 0 },
    font: { color: '#e7f0fb', family: 'Inter, sans-serif' }
  }, { responsive: true, displayModeBar: false });

  if (summary) {
    const recent = mapMeta.recent30 ?? 0;
    const prev = mapMeta.prev30 ?? 0;
    const delta = recent - prev;
    const sign = delta > 0 ? '+' : '';
    summary.textContent = `${mapMeta.totalIncidents ?? 0} incidents across ${mapMeta.totalStates ?? 0} states · 30d trend ${sign}${delta}`;
  }

  const movers = (mapMeta.topMovers || []).filter(m => (m.delta30 || 0) !== 0);
  renderMoverBadges(movers);

  chart.on('plotly_click', (event) => {
    const point = event?.points?.[0];
    const state = point?.location;
    if (state) loadStateCities(state);
  });
}

function setupMapControls() {
  const totalBtn = document.getElementById('metricTotalBtn');
  const recentBtn = document.getElementById('metricRecentBtn');
  if (!totalBtn || !recentBtn) return;

  const setActive = (metric) => {
    mapMetric = metric;
    totalBtn.classList.toggle('active', metric === 'count');
    recentBtn.classList.toggle('active', metric === 'recent30');
    drawMap();
  };

  totalBtn.addEventListener('click', () => setActive('count'));
  recentBtn.addEventListener('click', () => setActive('recent30'));
}

async function loadMap() {
  const chart = document.getElementById('usMapChart');
  const summary = document.getElementById('mapSummary');
  if (!chart || typeof Plotly === 'undefined') return;

  try {
    const res = await fetch('/api/us-map');
    const payload = await res.json();
    mapStates = payload.states || [];
    mapMeta = payload.summary || {};

    if (!mapStates.length) {
      if (summary) summary.textContent = 'Map data unavailable right now.';
      chart.innerHTML = '<div class="muted">Map data unavailable right now.</div>';
      return;
    }

    setupMapControls();
    await drawMap();
  } catch (_) {
    if (summary) summary.textContent = 'Map data unavailable right now.';
    chart.innerHTML = '<div class="muted">Map data unavailable right now.</div>';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadMeta();
  setupAutocomplete();
  loadMap();
});
