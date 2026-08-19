#!/usr/bin/env python3
"""
Holt Moritz' Übungsergebnisse aus Supabase (Tabelle pt_results) und gibt sie
im selben Textformat aus, das früher der "In Zwischenablage kopieren"-Knopf
erzeugt hat. Für Claude zum Lesen am Session-Start.

Aufruf:
  python3 tools/pull_results.py            # alle Ergebnisse
  python3 tools/pull_results.py --days 14  # nur die letzten 14 Tage
  python3 tools/pull_results.py --since 2026-08-01
  python3 tools/pull_results.py --json     # Rohdaten

Der Schlüssel ist der öffentliche "publishable key" (steht auch in js/progress.js).
"""
import argparse, json, sys, urllib.request, urllib.parse
from datetime import datetime, timedelta, timezone

URL   = "https://hbidncsgqxucqmubjdjq.supabase.co"
KEY   = "sb_publishable_7EqzzoyFyfvjHzLmvMOcTQ_-x1KqeFW"
TABLE = "pt_results"

def fetch(since=None, limit=1000):
    params = {
        "select": "id,created_at,client_ts,device,exercise_id,exercise_name,topic,total_score,total_count,pct,sections",
        "order": "created_at.asc",
        "limit": str(limit),
    }
    if since:
        params["created_at"] = "gte." + since
    q = urllib.parse.urlencode(params, safe=".,:+")
    req = urllib.request.Request(f"{URL}/rest/v1/{TABLE}?{q}", headers={"apikey": KEY, "Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))

def fmt_local(iso):
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone()
        return d.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return iso

def render(rows):
    if not rows:
        return "Keine Übungsergebnisse in Supabase."
    total_s = sum(r["total_score"] for r in rows)
    total_c = sum(r["total_count"] for r in rows)
    out = [f"=== PT-TEACHER FORTSCHRITT aus Supabase (Stand {datetime.now().strftime('%d.%m.%Y %H:%M')}) ===",
           f"{len(rows)} Übungen · Gesamt: {total_s}/{total_c} ({round(total_s / total_c * 100) if total_c else 0}%)", ""]
    # pro Thema
    by_topic = {}
    for r in rows:
        t = by_topic.setdefault(r["topic"] or "general", {"s": 0, "c": 0, "n": 0, "last": None})
        t["s"] += r["total_score"]; t["c"] += r["total_count"]; t["n"] += 1
        t["last"] = r["client_ts"] or r["created_at"]
    out.append("Nach Thema (schwächste zuerst):")
    for topic, t in sorted(by_topic.items(), key=lambda kv: (kv[1]["s"] / kv[1]["c"]) if kv[1]["c"] else 0):
        pct = round(t["s"] / t["c"] * 100) if t["c"] else 0
        out.append(f"  {pct:3d}%  {topic:<18} {t['n']}× · zuletzt {fmt_local(t['last'])}")
    out.append("")
    for r in rows:
        ts = r["client_ts"] or r["created_at"]
        out.append(f"--- {fmt_local(ts)} · {r['exercise_name'] or r['exercise_id']} · {r['total_score']}/{r['total_count']} ({r['pct']}%) [topic: {r['topic']}] [{r.get('device') or '?'}]")
        for sec in r.get("sections") or []:
            sp = round(sec["score"] / sec["total"] * 100) if sec.get("total") else 0
            mark = "✓" if sp >= 80 else "~" if sp >= 60 else "✗"
            out.append(f"  {mark} {sec.get('name')}: {sec.get('score')}/{sec.get('total')} ({sp}%)")
            for w in sec.get("wrong") or []:
                out.append(f"      \"{w.get('q')}\" → Antwort: {w.get('user') or '(leer)'} | richtig: {w.get('correct')}")
        out.append("")
    return "\n".join(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int)
    ap.add_argument("--since")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    since = a.since
    if a.days:
        since = (datetime.now(timezone.utc) - timedelta(days=a.days)).isoformat()
    try:
        rows = fetch(since)
    except Exception as e:
        print(f"Fehler beim Abruf: {e}", file=sys.stderr); sys.exit(1)
    print(json.dumps(rows, ensure_ascii=False, indent=1) if a.json else render(rows))

if __name__ == "__main__":
    main()
