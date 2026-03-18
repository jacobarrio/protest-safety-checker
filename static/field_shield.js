const STORAGE_KEYS = {
  session: 'fieldShield.session',
  timeline: 'fieldShield.timeline',
  queue: 'fieldShield.queue',
  lockCode: 'fieldShield.lockCode',
};

let state = {
  session: null,
  timeline: [],
  queue: [],
  panicLocked: false,
};

function nowIso() {
  return new Date().toISOString();
}

function genId() {
  try {
    if (window.crypto && typeof window.crypto.randomUUID === 'function') {
      return window.crypto.randomUUID();
    }
  } catch (_) {}
  return `id-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function safeParse(value, fallback) {
  try {
    return JSON.parse(value);
  } catch (_) {
    return fallback;
  }
}

function loadState() {
  state.session = safeParse(localStorage.getItem(STORAGE_KEYS.session), null);
  state.timeline = safeParse(localStorage.getItem(STORAGE_KEYS.timeline), []);
  state.queue = safeParse(localStorage.getItem(STORAGE_KEYS.queue), []);
}

function persistState() {
  localStorage.setItem(STORAGE_KEYS.session, JSON.stringify(state.session));
  localStorage.setItem(STORAGE_KEYS.timeline, JSON.stringify(state.timeline.slice(0, 100)));
  localStorage.setItem(STORAGE_KEYS.queue, JSON.stringify(state.queue.slice(0, 50)));
}

function addTimelineEvent(type, message, details = {}) {
  state.timeline.unshift({ id: genId(), type, message, details, createdAt: nowIso() });
  persistState();
  renderTimeline();
}

function renderTimeline() {
  const list = document.getElementById('timelineList');
  if (!list) return;

  if (!state.timeline.length) {
    list.innerHTML = '<li class="muted">No events yet. Start a session to begin tracking.</li>';
    return;
  }

  list.innerHTML = state.timeline.slice(0, 20).map((event) => {
    const t = new Date(event.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return `
      <li>
        <div class="event-type">${event.type.toUpperCase()} · ${t}</div>
        <div>${event.message}</div>
      </li>
    `;
  }).join('');
}

function setStatus(text) {
  const status = document.getElementById('sessionStatusText');
  if (status) status.textContent = text;
}

function updateOfflineBanner() {
  const banner = document.getElementById('offlineBanner');
  if (!banner) return;
  banner.hidden = navigator.onLine;
}

function setSessionControls() {
  const quickBtn = document.getElementById('quickCheckinBtn');
  if (quickBtn) quickBtn.disabled = !state.session;

  if (state.session) {
    setStatus(`Session active since ${new Date(state.session.startedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}.`);
  } else {
    setStatus('Session inactive. Start a session before logging field events.');
  }
}

async function postJson(url, payload) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`Request failed (${res.status})`);
  }

  return await res.json().catch(() => ({}));
}

function queueEvent(kind, payload) {
  state.queue.push({ id: genId(), kind, payload, queuedAt: nowIso() });
  persistState();
}

async function flushQueue() {
  if (!navigator.onLine || !state.queue.length) return;

  const remaining = [];
  for (const item of state.queue) {
    try {
      if (item.kind === 'checkin') {
        await postJson('/api/field-shield/checkin', item.payload);
      } else if (item.kind === 'incident') {
        await postJson('/api/field-shield/incident', item.payload);
      }
    } catch (_) {
      remaining.push(item);
    }
  }

  const flushedCount = state.queue.length - remaining.length;
  state.queue = remaining;
  persistState();

  if (flushedCount > 0) {
    addTimelineEvent('sync', `${flushedCount} queued event(s) synced after reconnect.`);
  }
}

async function startSession() {
  if (state.panicLocked) return;

  const payload = {
    organizer_alias: 'field-user',
    consent_ack: true,
    location: '',
    trusted_contacts: [],
  };

  try {
    const res = await postJson('/api/field-shield/start', payload);
    state.session = {
      id: res.session_id || genId(),
      startedAt: res.created_at || nowIso(),
      serverSynced: true,
    };
    addTimelineEvent('session', 'Session started and synced.');
  } catch (_) {
    state.session = { id: genId(), startedAt: nowIso(), serverSynced: false };
    addTimelineEvent('session', 'Session started locally (server unavailable).');
  }

  persistState();
  setSessionControls();
}

async function quickCheckin() {
  if (!state.session || state.panicLocked) return;

  const payload = {
    session_id: state.session.id,
    timestamp: nowIso(),
    status: 'ok',
  };

  if (!navigator.onLine) {
    queueEvent('checkin', payload);
    addTimelineEvent('checkin', 'Quick check-in saved offline.');
    return;
  }

  try {
    await postJson('/api/field-shield/checkin', payload);
    addTimelineEvent('checkin', 'Quick check-in sent.');
  } catch (_) {
    queueEvent('checkin', payload);
    addTimelineEvent('checkin', 'Check-in queued after sync error.');
  }
}

async function submitIncident(form) {
  if (!state.session || state.panicLocked) return;

  const formData = new FormData(form);
  const agentsCount = Number(formData.get('agentsCount') || 0);
  const vehiclesCount = Number(formData.get('vehiclesCount') || 0);
  const forceLevel = String(formData.get('forceLevel') || 'unknown');
  const notes = String(formData.get('notes') || '').trim();

  const payload = {
    session_id: state.session.id,
    timestamp: nowIso(),
    incident_type: forceLevel === 'physical' || forceLevel === 'less-lethal' ? 'assault' : 'other',
    severity: forceLevel === 'less-lethal' ? 5 : (forceLevel === 'physical' ? 4 : (forceLevel === 'presence' ? 2 : 3)),
    description: `Agents observed: ${agentsCount}; Vehicles observed: ${vehiclesCount}; Force level: ${forceLevel}. Notes: ${notes || 'none'}`,
    location: '',
  };

  if (!navigator.onLine) {
    queueEvent('incident', payload);
    addTimelineEvent('incident', `Incident queued offline (${payload.forceLevel}).`);
    form.reset();
    return;
  }

  try {
    await postJson('/api/field-shield/incident', payload);
    addTimelineEvent('incident', `Incident sent (${payload.forceLevel}).`);
  } catch (_) {
    queueEvent('incident', payload);
    addTimelineEvent('incident', `Incident queued after sync error (${payload.forceLevel}).`);
  }

  form.reset();
}

async function submitTrustedAlert(form) {
  if (!state.session || state.panicLocked) return;

  const formData = new FormData(form);
  const contactName = String(formData.get('contactName') || '').trim();
  const contactMethod = String(formData.get('contactMethod') || '').trim().toLowerCase();
  const message = String(formData.get('message') || '').trim();

  const providers = [];
  if (contactMethod.includes('signal')) providers.push('signal');
  if (contactMethod.includes('sms') || contactMethod.includes('text')) providers.push('sms');
  if (!providers.length) providers.push('sms');

  const payload = {
    session_id: state.session.id,
    timestamp: nowIso(),
    alert_type: 'distress',
    message,
    providers,
    recipients: [contactName],
  };

  try {
    await postJson('/api/field-shield/alert', payload);
    addTimelineEvent('alert', `Trusted alert sent to ${contactName || 'contact'}.`);
    form.reset();
  } catch (_) {
    addTimelineEvent('alert', 'Trusted alert could not be sent (server unavailable).');
  }
}

function enablePanicLock() {
  const existing = localStorage.getItem(STORAGE_KEYS.lockCode);
  if (!existing) {
    const candidate = prompt('Set a short unlock code for this device (visual lock only):');
    if (!candidate) return;
    localStorage.setItem(STORAGE_KEYS.lockCode, candidate);
  }

  state.panicLocked = true;
  document.getElementById('panicOverlay')?.removeAttribute('hidden');
}

function tryUnlock(code) {
  const savedCode = localStorage.getItem(STORAGE_KEYS.lockCode);
  if (!savedCode || code === savedCode) {
    state.panicLocked = false;
    document.getElementById('panicOverlay')?.setAttribute('hidden', 'hidden');
    return true;
  }
  return false;
}

function bindUI() {
  document.getElementById('startSessionBtn')?.addEventListener('click', startSession);
  document.getElementById('quickCheckinBtn')?.addEventListener('click', quickCheckin);
  document.getElementById('panicLockBtn')?.addEventListener('click', enablePanicLock);

  document.getElementById('incidentForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    await submitIncident(e.currentTarget);
  });

  document.getElementById('contactAlertForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    await submitTrustedAlert(e.currentTarget);
  });

  document.getElementById('unlockForm')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const input = document.getElementById('unlockCodeInput');
    if (!input) return;

    const ok = tryUnlock(input.value);
    input.value = '';
    if (!ok) alert('Unlock code mismatch.');
  });

  window.addEventListener('online', () => {
    updateOfflineBanner();
    flushQueue();
  });
  window.addEventListener('offline', updateOfflineBanner);
}

async function loadServerTimeline() {
  try {
    const res = await fetch('/api/field-shield/timeline');
    if (!res.ok) return;
    const data = await res.json();
    if (Array.isArray(data?.events) && data.events.length) {
      const merged = [...data.events, ...state.timeline].slice(0, 40);
      const deduped = [];
      const seen = new Set();
      for (const item of merged) {
        const key = `${item.type || 'event'}:${item.createdAt || item.timestamp || ''}:${item.message || ''}`;
        if (seen.has(key)) continue;
        seen.add(key);
        deduped.push({
          id: item.id || genId(),
          type: item.type || 'event',
          message: item.message || 'Field event logged.',
          createdAt: item.createdAt || item.timestamp || nowIso(),
        });
      }
      state.timeline = deduped.slice(0, 40);
      persistState();
    }
  } catch (_) {
    // server timeline optional
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  loadState();
  bindUI();
  setSessionControls();
  updateOfflineBanner();
  renderTimeline();

  await loadServerTimeline();
  renderTimeline();
  await flushQueue();
});
