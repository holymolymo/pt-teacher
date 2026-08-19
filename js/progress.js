/**
 * PT-Teacher Progress Tracking + Cloud-Sync (Supabase)
 *
 * Jede abgeschlossene Übung wird
 *   1. lokal gespeichert (localStorage, funktioniert auch offline) und
 *   2. an Supabase geschickt (Tabelle pt_results). Klappt das gerade nicht
 *      (kein Netz), bleibt der Eintrag in einer Warteschlange und wird beim
 *      nächsten Seitenaufruf oder sobald das Netz zurück ist nachgeschickt.
 *   3. Beim Öffnen holt sich die App außerdem alles aus Supabase, was lokal
 *      fehlt (neues Handy, gelöschter Browser-Speicher).
 *
 * Verwendung in jeder Übungs-Seite:
 *   <script src="js/progress.js"></script>
 *   PTProgress.save({ exerciseId, exerciseName, topic, sections: [{name, score, total, wrong: [{q,user,correct}]}] })
 *
 * Der Supabase-Schlüssel unten ist der öffentliche "publishable key". Er darf
 * hier stehen; die Tabelle ist per Row-Level-Security so eingestellt, dass die
 * App nur eintragen und lesen kann, nie ändern oder löschen.
 */

(function() {
  const STORAGE_KEY = 'pt_teacher_history';
  const QUEUE_KEY   = 'pt_teacher_sync_queue';   // Liste von client_ids, die noch nicht in Supabase sind
  const META_KEY    = 'pt_teacher_sync_meta';    // { lastPush, lastPull, lastError }
  const MAX_HISTORY = 500;

  // ---- Supabase ----
  const SB = {
    url: 'https://zhddqcgvrfhajbgpekon.supabase.co',
    key: 'sb_publishable_FuqpDPiql_-yAbBauzq06Q_of3BWnMd',
    table: 'pt_results'
  };
  const SB_HEADERS = { 'apikey': SB.key, 'Authorization': 'Bearer ' + SB.key, 'Content-Type': 'application/json' };

  // ---- lokale Historie ----
  function loadHistory() {
    try { const raw = localStorage.getItem(STORAGE_KEY); return raw ? JSON.parse(raw) : []; }
    catch (e) { console.warn('Progress-History corrupted, resetting.', e); return []; }
  }
  function saveHistory(history) {
    if (history.length > MAX_HISTORY) history = history.slice(-MAX_HISTORY);
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(history)); }
    catch (e) { console.error('Cannot save progress:', e); }
  }
  function loadJSON(key, fallback) { try { const r = localStorage.getItem(key); return r ? JSON.parse(r) : fallback; } catch (e) { return fallback; } }
  function saveJSON(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); } catch (e) {} }

  function makeClientId(ts) {
    return (ts || new Date().toISOString()).replace(/[-:.TZ]/g, '') + '-' + Math.random().toString(36).slice(2, 8);
  }
  function deviceLabel() {
    const ua = navigator.userAgent;
    const dev = /iPhone/.test(ua) ? 'iPhone' : /iPad/.test(ua) ? 'iPad' : /Android/.test(ua) ? 'Android' : /Macintosh/.test(ua) ? 'Mac' : /Windows/.test(ua) ? 'Windows' : 'Gerät';
    const br  = /CriOS|Chrome/.test(ua) ? 'Chrome' : /Safari/.test(ua) ? 'Safari' : /Firefox|FxiOS/.test(ua) ? 'Firefox' : 'Browser';
    const standalone = window.matchMedia && window.matchMedia('(display-mode: standalone)').matches;
    return dev + ' ' + br + (standalone ? ' (App)' : '');
  }

  // Alte Einträge ohne client_id nachträglich kennzeichnen (einmalig), damit sie gesynct werden können
  function ensureClientIds() {
    const history = loadHistory();
    let changed = false;
    history.forEach(h => {
      if (!h.clientId) { h.clientId = makeClientId(h.timestamp); changed = true; enqueue(h.clientId); }
    });
    if (changed) saveHistory(history);
  }

  // ---- Warteschlange ----
  function enqueue(clientId) {
    const q = loadJSON(QUEUE_KEY, []);
    if (q.indexOf(clientId) < 0) { q.push(clientId); saveJSON(QUEUE_KEY, q); }
  }
  function dequeue(clientId) {
    saveJSON(QUEUE_KEY, loadJSON(QUEUE_KEY, []).filter(id => id !== clientId));
  }
  function pendingCount() { return loadJSON(QUEUE_KEY, []).length; }
  function meta() { return loadJSON(META_KEY, {}); }
  function setMeta(patch) { saveJSON(META_KEY, Object.assign(meta(), patch)); }

  function toRow(h) {
    return {
      client_id: h.clientId, client_ts: h.timestamp, device: deviceLabel(),
      exercise_id: h.exerciseId, exercise_name: h.exerciseName, topic: h.topic,
      total_score: h.totalScore, total_count: h.totalCount, pct: h.pct, sections: h.sections || []
    };
  }
  function fromRow(r) {
    return {
      clientId: r.client_id, timestamp: r.client_ts || r.created_at,
      exerciseId: r.exercise_id, exerciseName: r.exercise_name || r.exercise_id, topic: r.topic || 'general',
      totalScore: r.total_score, totalCount: r.total_count, pct: r.pct, sections: r.sections || [], fromCloud: true
    };
  }

  let pushing = false;
  // Alles aus der Warteschlange an Supabase schicken. Gibt {sent, pending} zurück.
  async function syncNow() {
    if (pushing) return { sent: 0, pending: pendingCount(), busy: true };
    pushing = true;
    let sent = 0;
    try {
      const history = loadHistory();
      const byId = {}; history.forEach(h => { if (h.clientId) byId[h.clientId] = h; });
      const queue = loadJSON(QUEUE_KEY, []);
      for (const id of queue) {
        const h = byId[id];
        if (!h) { dequeue(id); continue; }          // gibt es lokal nicht mehr
        const res = await fetch(SB.url + '/rest/v1/' + SB.table + '?on_conflict=client_id', {
          method: 'POST', headers: Object.assign({ 'Prefer': 'resolution=ignore-duplicates' }, SB_HEADERS),
          body: JSON.stringify(toRow(h))
        });
        if (res.ok || res.status === 409) { dequeue(id); sent++; }
        else { throw new Error('Supabase ' + res.status); }
      }
      setMeta({ lastPush: new Date().toISOString(), lastError: null });
    } catch (e) {
      setMeta({ lastError: String(e && e.message || e), lastErrorAt: new Date().toISOString() });
    } finally { pushing = false; }
    document.dispatchEvent(new CustomEvent('ptprogress:synced', { detail: { sent, pending: pendingCount() } }));
    return { sent, pending: pendingCount() };
  }

  // Aus Supabase holen, was lokal fehlt (z. B. neues Gerät). Gibt Anzahl neuer Einträge zurück.
  async function pullFromCloud(opts) {
    opts = opts || {};
    const m = meta();
    if (!opts.force && m.lastPull && (Date.now() - new Date(m.lastPull).getTime()) < 30 * 60 * 1000) return 0; // max. alle 30 Min
    try {
      const res = await fetch(SB.url + '/rest/v1/' + SB.table + '?select=client_id,client_ts,created_at,exercise_id,exercise_name,topic,total_score,total_count,pct,sections&order=created_at.asc&limit=' + MAX_HISTORY, { headers: SB_HEADERS });
      if (!res.ok) throw new Error('Supabase ' + res.status);
      const rows = await res.json();
      const history = loadHistory();
      const have = {}; history.forEach(h => { if (h.clientId) have[h.clientId] = true; });
      let added = 0;
      rows.forEach(r => { if (r.client_id && !have[r.client_id]) { history.push(fromRow(r)); added++; } });
      if (added) {
        history.sort((a, b) => (a.timestamp || '').localeCompare(b.timestamp || ''));
        saveHistory(history);
      }
      setMeta({ lastPull: new Date().toISOString(), lastError: null });
      if (added) document.dispatchEvent(new CustomEvent('ptprogress:pulled', { detail: { added } }));
      return added;
    } catch (e) {
      setMeta({ lastError: String(e && e.message || e), lastErrorAt: new Date().toISOString() });
      return 0;
    }
  }

  function syncStatus() {
    const m = meta();
    return { pending: pendingCount(), lastPush: m.lastPush || null, lastPull: m.lastPull || null, lastError: m.lastError || null, online: navigator.onLine !== false };
  }

  // ---- öffentliche API ----
  function save(entry) {
    if (!entry.exerciseId || !entry.sections) { console.warn('PTProgress.save: exerciseId and sections required'); return; }
    const timestamp = new Date().toISOString();
    const totalScore = entry.sections.reduce((s, sec) => s + sec.score, 0);
    const totalCount = entry.sections.reduce((s, sec) => s + sec.total, 0);
    const record = {
      clientId: makeClientId(timestamp), timestamp,
      exerciseId: entry.exerciseId, exerciseName: entry.exerciseName || entry.exerciseId, topic: entry.topic || 'general',
      totalScore, totalCount, pct: totalCount ? Math.round(totalScore / totalCount * 100) : 0,
      sections: entry.sections
    };
    const history = loadHistory();
    history.push(record);
    saveHistory(history);
    enqueue(record.clientId);
    syncNow();                     // im Hintergrund, blockiert nichts
    return record;
  }

  function getAll() { return loadHistory(); }

  function clear() {
    if (confirm('Lokale Übungs-Ergebnisse auf diesem Gerät löschen? (In der Cloud bleiben sie erhalten und werden beim nächsten Öffnen wieder geladen.)')) {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(QUEUE_KEY);
      localStorage.removeItem(META_KEY);
      return true;
    }
    return false;
  }

  /** Ergebnisse als kompakter Text, zum Kopieren und in Claude einfügen (Notlösung, falls der Sync mal hakt). */
  function formatForClaude() {
    const history = loadHistory();
    if (!history.length) return 'Noch keine Übungs-Ergebnisse.';
    const now = new Date();
    let out = `=== PT-TEACHER FORTSCHRITT (Export: ${now.toLocaleString('de-DE')}) ===\n`;
    out += `${history.length} Übungen absolviert · `;
    const overallScore = history.reduce((s, h) => s + h.totalScore, 0);
    const overallTotal = history.reduce((s, h) => s + h.totalCount, 0);
    out += `Gesamt: ${overallScore}/${overallTotal} (${Math.round(overallScore/overallTotal*100)}%)\n\n`;
    history.forEach(h => {
      const date = new Date(h.timestamp);
      const dateStr = date.toLocaleDateString('de-DE') + ' ' + date.toLocaleTimeString('de-DE', {hour:'2-digit', minute:'2-digit'});
      out += `--- ${dateStr} · ${h.exerciseName} · ${h.totalScore}/${h.totalCount} (${h.pct}%) [topic: ${h.topic}]\n`;
      (h.sections || []).forEach(sec => {
        const secPct = sec.total ? Math.round(sec.score/sec.total*100) : 0;
        const mark = secPct >= 80 ? '✓' : secPct >= 60 ? '~' : '✗';
        out += `  ${mark} ${sec.name}: ${sec.score}/${sec.total} (${secPct}%)\n`;
        (sec.wrong || []).forEach(w => { out += `      "${w.q}" → deine Antwort: ${w.user || '(leer)'} | richtig: ${w.correct}\n`; });
      });
      out += '\n';
    });
    return out;
  }

  async function copyToClipboard() {
    const text = formatForClaude();
    try { await navigator.clipboard.writeText(text); return true; }
    catch (e) {
      const ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.left = '-9999px';
      document.body.appendChild(ta); ta.select();
      const ok = document.execCommand('copy');
      document.body.removeChild(ta);
      return ok;
    }
  }

  function downloadAsFile() {
    const blob = new Blob([formatForClaude()], {type: 'text/plain'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `pt-teacher-fortschritt-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function summaryByTopic() {
    const history = loadHistory();
    const bytopic = {};
    history.forEach(h => {
      if (!bytopic[h.topic]) bytopic[h.topic] = { score: 0, total: 0, exercises: 0, latestPct: 0, latestDate: null };
      bytopic[h.topic].score += h.totalScore;
      bytopic[h.topic].total += h.totalCount;
      bytopic[h.topic].exercises++;
      if (!bytopic[h.topic].latestDate || h.timestamp > bytopic[h.topic].latestDate) {
        bytopic[h.topic].latestDate = h.timestamp;
        bytopic[h.topic].latestPct = h.pct;
      }
    });
    Object.values(bytopic).forEach(t => t.avgPct = t.total ? Math.round(t.score/t.total*100) : 0);
    return bytopic;
  }

  window.PTProgress = { save, getAll, clear, formatForClaude, copyToClipboard, downloadAsFile, summaryByTopic,
                        syncNow, pullFromCloud, syncStatus, SUPABASE: { url: SB.url, table: SB.table } };

  // ---- Start: alte Einträge kennzeichnen, Warteschlange abarbeiten, Fehlendes holen ----
  ensureClientIds();
  function boot() {
    syncNow();
    pullFromCloud();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
  window.addEventListener('online', function () { syncNow(); });
})();
