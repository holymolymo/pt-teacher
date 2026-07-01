/**
 * PT-Teacher Progress Tracking
 *
 * Verwendung in jeder Übungs-Seite:
 *   1. <script src="js/progress.js"></script>
 *   2. Nach Auswertung aufrufen:
 *      PTProgress.save({
 *        exerciseId: 'perfeito-tempus-v1',
 *        exerciseName: 'Pretérito Perfeito — Tempuslücke',
 *        topic: 'perfeito',
 *        sections: [{
 *          name: 'Tempus wählen',
 *          score: 6, total: 10,
 *          wrong: [{ q: 'Ontem eu ___', user: 'vou', correct: 'fui' }]
 *        }, ...]
 *      });
 */

(function() {
  const STORAGE_KEY = 'pt_teacher_history';
  const MAX_HISTORY = 100;

  function loadHistory() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      console.warn('Progress-History corrupted, resetting.', e);
      return [];
    }
  }

  function saveHistory(history) {
    if (history.length > MAX_HISTORY) history = history.slice(-MAX_HISTORY);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    } catch (e) {
      console.error('Cannot save progress:', e);
    }
  }

  function save(entry) {
    if (!entry.exerciseId || !entry.sections) {
      console.warn('PTProgress.save: exerciseId and sections required');
      return;
    }
    const timestamp = new Date().toISOString();
    const totalScore = entry.sections.reduce((s, sec) => s + sec.score, 0);
    const totalCount = entry.sections.reduce((s, sec) => s + sec.total, 0);
    const record = {
      timestamp,
      exerciseId: entry.exerciseId,
      exerciseName: entry.exerciseName || entry.exerciseId,
      topic: entry.topic || 'general',
      totalScore,
      totalCount,
      pct: totalCount ? Math.round(totalScore / totalCount * 100) : 0,
      sections: entry.sections
    };
    const history = loadHistory();
    history.push(record);
    saveHistory(history);
    return record;
  }

  function getAll() { return loadHistory(); }

  function clear() {
    if (confirm('Alle Übungs-Ergebnisse wirklich löschen?')) {
      localStorage.removeItem(STORAGE_KEY);
      return true;
    }
    return false;
  }

  /**
   * Ergebnisse als kompakter Text — zum Kopieren + in Claude einfügen.
   */
  function formatForClaude() {
    const history = loadHistory();
    if (!history.length) return 'Noch keine Übungs-Ergebnisse.';

    const now = new Date();
    let out = `=== PT-TEACHER FORTSCHRITT (Export: ${now.toLocaleString('de-DE')}) ===\n`;
    out += `${history.length} Übungen absolviert · `;
    const overallScore = history.reduce((s, h) => s + h.totalScore, 0);
    const overallTotal = history.reduce((s, h) => s + h.totalCount, 0);
    out += `Gesamt: ${overallScore}/${overallTotal} (${Math.round(overallScore/overallTotal*100)}%)\n\n`;

    // Pro Übung (chronologisch, neueste zuletzt)
    history.forEach(h => {
      const date = new Date(h.timestamp);
      const dateStr = date.toLocaleDateString('de-DE') + ' ' +
        date.toLocaleTimeString('de-DE', {hour:'2-digit', minute:'2-digit'});
      out += `--- ${dateStr} · ${h.exerciseName} · ${h.totalScore}/${h.totalCount} (${h.pct}%) [topic: ${h.topic}]\n`;
      h.sections.forEach(sec => {
        const secPct = sec.total ? Math.round(sec.score/sec.total*100) : 0;
        const mark = secPct >= 80 ? '✓' : secPct >= 60 ? '~' : '✗';
        out += `  ${mark} ${sec.name}: ${sec.score}/${sec.total} (${secPct}%)\n`;
        if (sec.wrong && sec.wrong.length) {
          sec.wrong.forEach(w => {
            out += `      "${w.q}" → deine Antwort: ${w.user || '(leer)'} | richtig: ${w.correct}\n`;
          });
        }
      });
      out += '\n';
    });

    return out;
  }

  async function copyToClipboard() {
    const text = formatForClaude();
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (e) {
      // Fallback: temporäres Textarea
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.left = '-9999px';
      document.body.appendChild(ta);
      ta.select();
      const ok = document.execCommand('copy');
      document.body.removeChild(ta);
      return ok;
    }
  }

  function downloadAsFile() {
    const text = formatForClaude();
    const blob = new Blob([text], {type: 'text/plain'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pt-teacher-fortschritt-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // Aggregate pro Topic für Dashboard-Anzeige
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

  window.PTProgress = { save, getAll, clear, formatForClaude, copyToClipboard, downloadAsFile, summaryByTopic };
})();
