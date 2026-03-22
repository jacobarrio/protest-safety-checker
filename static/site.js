async function loadMeta() {
  try {
    const [summaryRes, updatedRes, integrityRes] = await Promise.all([
      fetch('/api/data_summary'),
      fetch('/api/last_updated'),
      fetch('/api/data-integrity'),
    ]);
    const summary = await summaryRes.json();
    const updated = await updatedRes.json();
    const integrity = await integrityRes.json();

    const incidentCount = summary.total_incidents ?? summary.total_records ?? '—';
    const cityCount = summary.unique_locations ?? summary.unique_cities ?? '—';

    const i = document.getElementById('metaIncidents');
    const c = document.getElementById('metaCities');
    const u = document.getElementById('metaUpdated');
    if (i) i.textContent = incidentCount;
    if (c) c.textContent = cityCount;
    if (u) u.textContent = updated.display || updated.time_str || updated.timestamp || 'Unknown';

    const statusEl = document.getElementById('integrityStatus');
    const latestEl = document.getElementById('integrityLatest');
    const verifiedEl = document.getElementById('integrityVerified');
    const noteEl = document.getElementById('integrityNote');

    if (statusEl) {
      const status = (integrity.status || 'unknown').toLowerCase();
      statusEl.textContent = status.toUpperCase();
      statusEl.classList.remove('status-fresh', 'status-aging', 'status-stale', 'status-unknown');
      statusEl.classList.add(`status-${status}`);
    }
    if (latestEl) latestEl.textContent = integrity.latest_incident_date || 'Unknown';
    if (verifiedEl) verifiedEl.textContent = integrity.verified_on || 'Unknown';

    if (noteEl) {
      const staleDays = integrity.days_since_latest;
      const coverage = integrity.source_url_coverage_pct;
      const dupes = integrity.duplicate_rows;
      if (integrity.status === 'stale') {
        noteEl.textContent = `Dataset is stale (${staleDays} days since latest incident in dataset). Source URL coverage: ${coverage}% · duplicate rows: ${dupes}.`;
      } else if (integrity.status === 'aging') {
        noteEl.textContent = `Dataset is aging (${staleDays} days since latest incident). Source URL coverage: ${coverage}% · duplicate rows: ${dupes}.`;
      } else if (integrity.status === 'fresh') {
        noteEl.textContent = `Dataset is fresh (${staleDays} days since latest incident). Source URL coverage: ${coverage}% · duplicate rows: ${dupes}.`;
      } else {
        noteEl.textContent = 'Integrity status unavailable right now.';
      }
    }
  } catch (_) {}
}

let currentRole = 'organizer';

function getRoleLabel(role) {
  return {
    organizer: 'Organizer',
    legal: 'Legal Observer',
    journalist: 'Journalist',
    public: 'General Public',
  }[role] || 'Organizer';
}

function dedupePlanItems(items, maxItems = 3) {
  const picked = [];
  const usedCategories = new Set();
  const usedText = new Set();

  for (const item of items) {
    const text = (item.text || '').trim();
    if (!text) continue;
    const norm = text.toLowerCase().replace(/[^a-z0-9 ]/g, '').replace(/\s+/g, ' ').trim();
    if (usedText.has(norm)) continue;

    if (!usedCategories.has(item.category)) {
      picked.push(text);
      usedCategories.add(item.category);
      usedText.add(norm);
    }

    if (picked.length >= maxItems) break;
  }

  if (picked.length < maxItems) {
    for (const item of items) {
      const text = (item.text || '').trim();
      const norm = text.toLowerCase().replace(/[^a-z0-9 ]/g, '').replace(/\s+/g, ' ').trim();
      if (!text || usedText.has(norm)) continue;
      picked.push(text);
      usedText.add(norm);
      if (picked.length >= maxItems) break;
    }
  }

  return picked;
}

function buildPlan(data, role) {
  const level = (data.risk_level || '').toLowerCase();
  const high = level === 'high';
  const medium = level === 'medium';

  const baseNow = high
    ? [
      { category: 'movement', text: 'Switch to a lower-exposure route now.' },
      { category: 'roles', text: 'Move legal + de-escalation roles to the front.' },
      { category: 'comms', text: 'Run comms check-ins every 10 minutes.' }
    ]
    : medium
      ? [
        { category: 'movement', text: 'Keep your group tight and visible.' },
        { category: 'fallback', text: 'Set one fallback regroup point.' },
        { category: 'comms', text: 'Run a 15-minute check-in loop.' }
      ]
      : [
        { category: 'roles', text: 'Keep normal safety roles active.' },
        { category: 'movement', text: 'Confirm meetup and exits before movement.' },
        { category: 'monitoring', text: 'Re-check risk if conditions shift.' }
      ];

  const baseAvoid = high
    ? [
      { category: 'exposure', text: 'Do not post your live location publicly.' },
      { category: 'comms', text: 'Do not split people without comms.' },
      { category: 'movement', text: 'Do not rely on only one exit route.' }
    ]
    : medium
      ? [
        { category: 'movement', text: 'Avoid unnecessary linger points.' },
        { category: 'exposure', text: 'Avoid publishing faces in real time.' },
        { category: 'comms', text: 'Avoid single-point comms failure.' }
      ]
      : [
        { category: 'complacency', text: 'Avoid complacency.' },
        { category: 'exposure', text: 'Avoid sharing sensitive details in open chat.' },
        { category: 'comms', text: 'Avoid skipping buddy check-ins.' }
      ];

  const roleAdd = {
    organizer: {
      now: [{ category: 'command', text: 'Assign one person to route updates.' }, { category: 'fallback', text: 'Prep a regroup message before movement.' }],
      avoid: [{ category: 'command', text: 'Do not change plan without broadcasting it clearly.' }]
    },
    legal: {
      now: [{ category: 'evidence', text: 'Start timestamped observation notes now.' }, { category: 'handoff', text: 'Confirm witness handoff channel.' }],
      avoid: [{ category: 'lane', text: 'Do not operate without a clear observation lane.' }]
    },
    journalist: {
      now: [{ category: 'coverage', text: 'Capture context shots before close coverage.' }, { category: 'backup', text: 'Keep one backup uploader offsite.' }],
      avoid: [{ category: 'exposure', text: 'Do not publish identifying faces without review.' }]
    },
    public: {
      now: [{ category: 'comms', text: 'Share your check-in plan with one trusted contact.' }, { category: 'contacts', text: 'Keep emergency contacts pinned.' }],
      avoid: [{ category: 'movement', text: 'Do not go alone without a comms plan.' }]
    }
  };

  const extra = roleAdd[role] || roleAdd.organizer;
  const now = dedupePlanItems([...baseNow, ...extra.now], 3);
  const avoid = dedupePlanItems([...baseAvoid, ...extra.avoid], 3);

  const city = data.resolved_location || data.query_input || 'this area';
  const intro = `${getRoleLabel(role)} mode · ${data.risk_level || 'Unknown'} risk in ${city}. Do the next 30 minutes deliberately.`;
  const share = `${getRoleLabel(role)} plan for ${city}\nRisk: ${data.risk_level || 'Unknown'} (${data.risk_score ?? '—'}/100)\nDo now: ${now.join(' | ')}\nAvoid: ${avoid.join(' | ')}`;

  return { intro, now, avoid, share };
}

function renderPlan(plan) {
  const intro = document.getElementById('planIntro');
  const now = document.getElementById('planNow');
  const avoid = document.getElementById('planAvoid');
  const share = document.getElementById('planShare');

  if (intro) intro.textContent = plan.intro;
  if (now) now.innerHTML = plan.now.map(x => `<li>${x}</li>`).join('');
  if (avoid) avoid.innerHTML = plan.avoid.map(x => `<li>${x}</li>`).join('');
  if (share) share.value = plan.share;
}

function setupRoleChips() {
  const chips = Array.from(document.querySelectorAll('.role-chip'));
  if (!chips.length) return;

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      currentRole = chip.dataset.role || 'organizer';
      chips.forEach(c => c.classList.toggle('active', c === chip));
      const visible = document.getElementById('riskResult')?.classList.contains('show');
      if (visible) checkRisk();
    });
  });
}

function setupCopyPlan() {
  const btn = document.getElementById('copyPlanBtn');
  const box = document.getElementById('planShare');
  if (!btn || !box) return;

  btn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(box.value || '');
      btn.textContent = 'Copied';
      setTimeout(() => { btn.textContent = 'Copy plan text'; }, 1000);
    } catch (_) {
      box.select();
      document.execCommand('copy');
      btn.textContent = 'Copied';
      setTimeout(() => { btn.textContent = 'Copy plan text'; }, 1000);
    }
  });
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
      const hasCap = typeof c.cap !== 'undefined' && typeof c.capped_score !== 'undefined';
      if (hasCap) {
        return `<li>${c.name}: ${c.count} × ${c.weight} = ${c.raw_score} → capped at ${c.capped_score} (max ${c.cap})</li>`;
      }
      return `<li>${c.name}: ${c.count} × ${c.weight} = ${c.raw_score}</li>`;
    }).join('');

    const plan = buildPlan(data, currentRole);
    renderPlan(plan);

    output.classList.add('show');
  } catch (e) {
    document.getElementById('riskLevel').textContent = 'Error';
    document.getElementById('riskScore').textContent = 'Could not fetch risk data.';
    document.getElementById('riskResolved').textContent = '';
    document.getElementById('riskConfidence').textContent = '';
    document.getElementById('riskDrivers').innerHTML = '';
    document.getElementById('riskBreakdown').innerHTML = '';
    renderPlan({
      intro: 'Could not generate a plan from this query. Try a nearby city.',
      now: ['Retry with city + state format.', 'Check local channels for updates.'],
      avoid: ['Avoid acting on stale assumptions.'],
      share: 'Plan unavailable right now. Re-run with a clearer location.'
    });
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
  setupRoleChips();
  setupCopyPlan();
  loadMap();
});
