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
    if (u) u.textContent = updated.last_updated || updated.date || 'Unknown';
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

document.addEventListener('DOMContentLoaded', () => {
  loadMeta();
  setupAutocomplete();
});
