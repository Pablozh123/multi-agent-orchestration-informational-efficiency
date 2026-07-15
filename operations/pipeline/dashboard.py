"""Run-Dashboard: rekonstruiert alle Bot-Runs aus den Logs und rendert
eine filterbare HTML-Uebersicht (data/live/dashboard.html).

Quellen je Profil-Verzeichnis unter data/live/:
- bot_events.jsonl   (Drops, Entscheidungen, Fehler, Verkaeufe)
- decisions_log.jsonl (Orders mit Buch-Snapshots)
- run_annotationen.json (manuelle Einordnung: echt/fehltrigger, Notizen)

Aufloesungs-Status der gehandelten Maerkte wird live von Gamma geholt
(--offline ueberspringt das). Aufruf:
  python -m operations.pipeline.dashboard [--offline]
"""

from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LIVE_DIR = REPO_ROOT / "data" / "live"
ANNOT_PFAD = LIVE_DIR / "run_annotationen.json"
AUSGABE = LIVE_DIR / "dashboard.html"

PROFIL_NAMEN = {
    "allin_july3": "All-In july-3",
    "allin_july10": "All-In july-10",
    "jre_july6": "JRE july-6",
    "mrbeast_next": "MrBeast",
}


def _lade_jsonl(pfad: Path) -> list[dict]:
    if not pfad.exists():
        return []
    with open(pfad, encoding="utf-8") as f:
        return [json.loads(z) for z in f if z.strip()]


def rekonstruiere_runs() -> list[dict]:
    """Ein Run = drop_erkannt bis fertig/naechster Drop, je Profil."""
    runs = []
    for verzeichnis in sorted(LIVE_DIR.iterdir()):
        if not verzeichnis.is_dir():
            continue
        profil = verzeichnis.name
        events = _lade_jsonl(verzeichnis / "bot_events.jsonl")
        decisions = _lade_jsonl(verzeichnis / "decisions_log.jsonl")
        drops = [i for i, e in enumerate(events) if e["art"] == "drop_erkannt"]
        for idx, start_i in enumerate(drops):
            ende_i = drops[idx + 1] if idx + 1 < len(drops) else len(events)
            block = events[start_i:ende_i]
            drop = block[0]
            fertig = next((e for e in block if e["art"] == "fertig"), None)
            fehler = [e for e in block if e["art"] == "fehler"]
            t0, t1 = drop["wall_ts_utc"], (fertig or block[-1])["wall_ts_utc"]
            fills = [
                d for d in decisions
                if t0 <= d["wall_ts_utc"] <= t1
                and d["result"]["status"] in ("live_fill", "live_partial")
            ]
            fill_zeilen = [{
                "markt": d["decision"]["market_id"],
                "aktion": d["result"]["action"],
                "shares": d["result"]["size_shares"],
                "usd_log": d["result"]["size_usd"],
            } for d in fills]
            order_fehler = [
                d for d in decisions
                if t0 <= d["wall_ts_utc"] <= t1
                and d["result"]["status"] == "error"
            ]
            dauer_s = None
            if fertig:
                a = datetime.fromisoformat(t0.replace("Z", "+00:00"))
                b = datetime.fromisoformat(t1.replace("Z", "+00:00"))
                dauer_s = int((b - a).total_seconds())
            endstaende = (fertig or {}).get("endstaende", {})
            treffer = {k.split("will-")[-1].split("-be-said")[0]: v
                       for k, v in endstaende.items() if v > 0}
            runs.append({
                "profil": profil,
                "drop_ts": t0,
                "quelle": drop.get("quelle", "?"),
                "titel": drop.get("titel", ""),
                "dauer_s": dauer_s,
                "fills": fill_zeilen,
                "n_orderfehler": len(order_fehler),
                "n_laufzeitfehler": len(fehler),
                "treffer": treffer,
                "ausgegeben_usd": (fertig or {}).get("ausgegeben_usd"),
            })
    runs.sort(key=lambda r: r["drop_ts"])
    return runs


def hole_aufloesungen(markt_ids: set[str]) -> dict:
    """closed/outcome je Markt-ID von Gamma (best effort)."""
    import httpx

    out = {}
    for mid in markt_ids:
        try:
            m = httpx.get(f"https://gamma-api.polymarket.com/markets/{mid}",
                          headers={"User-Agent": "Mozilla/5.0"}, timeout=15).json()
            op = m.get("outcomePrices")
            op = json.loads(op) if isinstance(op, str) else (op or [])
            out[mid] = {
                "frage": m.get("question", ""),
                "closed": bool(m.get("closed")),
                "yes_gewann": bool(op) and float(op[0]) > 0.99,
            }
        except Exception:  # noqa: BLE001
            out[mid] = {"frage": "", "closed": False, "yes_gewann": None}
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--offline", action="store_true",
                        help="keine Gamma-Abfragen (Aufloesung unbekannt)")
    argv = parser.parse_args()

    runs = rekonstruiere_runs()
    annot = {}
    if ANNOT_PFAD.exists():
        annot = json.load(open(ANNOT_PFAD, encoding="utf-8")).get("runs", {})

    markt_ids = {f["markt"] for r in runs for f in r["fills"]}
    aufloesungen = {} if argv.offline else hole_aufloesungen(markt_ids)

    karten = []
    summe_pnl = 0.0
    n_echt = n_fehl = n_fills = 0
    for r in runs:
        schluessel = f"{r['profil']}|{r['drop_ts']}"
        a = annot.get(schluessel, {})
        status = a.get("status", "unklassifiziert")
        if status == "echt":
            n_echt += 1
        elif status == "fehltrigger":
            n_fehl += 1
        pnl = a.get("pnl_realisiert_usd")
        if pnl is not None:
            summe_pnl += pnl
        n_fills += len(r["fills"])

        fill_html = ""
        for f in r["fills"]:
            m = aufloesungen.get(f["markt"], {})
            if m.get("closed"):
                erg = "gewonnen" if (f["aktion"] == "YES") == m["yes_gewann"] else "verloren"
                erg_cls = "gut" if erg == "gewonnen" else "schlecht"
            else:
                erg, erg_cls = "offen", "neutral"
            frage = html.escape((m.get("frage") or f["markt"])[:58])
            fill_html += (
                f'<tr><td>{f["aktion"]}</td><td>{frage}</td>'
                f'<td class="num">{f["shares"]}</td>'
                f'<td><span class="pill {erg_cls}">{erg}</span></td></tr>'
            )
        if not fill_html:
            fill_html = '<tr><td colspan="4" class="stumm">keine Trades</td></tr>'

        treffer_txt = ", ".join(f"{k} {v}" for k, v in sorted(
            r["treffer"].items(), key=lambda x: -x[1])[:8]) or "keine"
        lehren = "".join(f"<li>{html.escape(l)}</li>" for l in a.get("lehren", []))
        dauer = f"{r['dauer_s']} s" if r["dauer_s"] is not None else "abgebrochen"
        pnl_txt = (f"{pnl:+.2f} USD" if pnl is not None else "offen")
        karten.append(f"""
<article class="run" data-profil="{r['profil']}" data-status="{status}"
         data-trades="{'ja' if r['fills'] else 'nein'}">
  <header>
    <span class="pill {'gut' if status == 'echt' else 'schlecht' if status == 'fehltrigger' else 'neutral'}">{status.upper()}</span>
    <h3>{html.escape(a.get('episode', r['titel'] or '?'))}</h3>
    <span class="mono">{r['drop_ts'][:16].replace('T', ' ')} UTC</span>
  </header>
  <div class="meta">
    <span>{PROFIL_NAMEN.get(r['profil'], r['profil'])}</span>
    <span>Quelle: <b>{html.escape(r['quelle'])}</b></span>
    <span>Drop bis fertig: <b>{dauer}</b></span>
    <span>PnL realisiert: <b>{pnl_txt}</b></span>
    <span>Orderfehler: {r['n_orderfehler']}</span>
  </div>
  <p class="notiz">{html.escape(a.get('notiz', ''))}</p>
  <table><tr><th>Seite</th><th>Markt</th><th>Shares</th><th>Ausgang</th></tr>{fill_html}</table>
  <p class="stumm klein">Zaehlstaende (Top): {html.escape(treffer_txt)}</p>
  {f'<ul class="lehren">{lehren}</ul>' if lehren else ''}
</article>""")

    erzeugt = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    seite = f"""<title>Mentions-Bot — Run-Uebersicht</title>
<style>
  :root {{ --papier:#f4f6f5; --karte:#fcfdfd; --tinte:#16211d; --tinte2:#47554f;
    --linie:#d8dedb; --gruen:#0e7b5b; --gruenhell:#e3f0ea; --rot:#a8402f;
    --rothell:#f6e3de; --warn:#a06614;
    --mono:"Cascadia Code",Consolas,ui-monospace,monospace;
    --sans:"Segoe UI",-apple-system,Arial,sans-serif; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--papier); color:var(--tinte);
    font-family:var(--sans); font-size:15.5px; line-height:1.5; }}
  .huelle {{ max-width:880px; margin:0 auto; padding:40px 20px 80px; }}
  .eyebrow {{ font-family:var(--mono); font-size:11.5px; letter-spacing:.13em;
    text-transform:uppercase; color:var(--gruen); font-weight:600; }}
  h1 {{ font-size:clamp(24px,4vw,34px); margin:6px 0 18px; letter-spacing:-.02em; }}
  .kennzahlen {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr));
    gap:1px; background:var(--linie); border:1px solid var(--linie);
    border-radius:6px; overflow:hidden; margin-bottom:26px; }}
  .kz {{ background:var(--karte); padding:12px 14px; }}
  .kz b {{ display:block; font-family:var(--mono); font-size:20px;
    font-variant-numeric:tabular-nums; }}
  .kz span {{ font-size:12px; color:var(--tinte2); }}
  .filter {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:22px; }}
  .filter button {{ font-family:var(--mono); font-size:12.5px; padding:6px 12px;
    border-radius:4px; border:1px solid var(--linie); background:var(--karte);
    color:var(--tinte2); cursor:pointer; }}
  .filter button.aktiv {{ background:var(--gruen); color:#fff; border-color:var(--gruen); }}
  .filter button:focus-visible {{ outline:2px solid var(--gruen); outline-offset:2px; }}
  .run {{ background:var(--karte); border:1px solid var(--linie); border-radius:6px;
    padding:18px 20px; margin-bottom:16px; }}
  .run header {{ display:flex; flex-wrap:wrap; align-items:baseline; gap:10px; }}
  .run h3 {{ margin:0; font-size:16.5px; flex:1 1 auto; }}
  .mono {{ font-family:var(--mono); font-size:12px; color:var(--tinte2); }}
  .pill {{ font-family:var(--mono); font-size:11px; font-weight:700;
    padding:3px 9px; border-radius:3px; white-space:nowrap; }}
  .pill.gut {{ background:var(--gruenhell); color:var(--gruen); }}
  .pill.schlecht {{ background:var(--rothell); color:var(--rot); }}
  .pill.neutral {{ background:#e9edeb; color:var(--tinte2); }}
  .meta {{ display:flex; flex-wrap:wrap; gap:6px 18px; font-size:13px;
    color:var(--tinte2); margin:10px 0 8px; }}
  .notiz {{ margin:8px 0; max-width:74ch; }}
  table {{ width:100%; border-collapse:collapse; font-size:13.5px; margin:10px 0 6px; }}
  th {{ text-align:left; font-family:var(--mono); font-size:10.5px;
    text-transform:uppercase; letter-spacing:.08em; color:var(--tinte2);
    padding:5px 8px; border-bottom:1px solid var(--linie); }}
  td {{ padding:6px 8px; border-bottom:1px solid #eef1f0; }}
  td.num {{ font-family:var(--mono); font-variant-numeric:tabular-nums; }}
  .stumm {{ color:var(--tinte2); }} .klein {{ font-size:12.5px; margin:6px 0 0; }}
  .lehren {{ margin:8px 0 0; padding-left:18px; font-size:13px; color:var(--warn); }}
  .fuss {{ margin-top:36px; font-family:var(--mono); font-size:12px; color:var(--tinte2); }}
</style>
<div class="huelle">
  <div class="eyebrow">Privater Mentions-Bot · Run-Dokumentation</div>
  <h1>Alle Runs, Trades und Lehren</h1>
  <div class="kennzahlen">
    <div class="kz"><b>{len(runs)}</b><span>Runs gesamt</span></div>
    <div class="kz"><b>{n_echt}</b><span>echte Episoden</span></div>
    <div class="kz"><b>{n_fehl}</b><span>Fehltrigger</span></div>
    <div class="kz"><b>{n_fills}</b><span>Fills</span></div>
    <div class="kz"><b>{summe_pnl:+.1f}</b><span>realisierte PnL (USD)</span></div>
  </div>
  <div class="filter" id="filter">
    <button data-f="alle" class="aktiv">Alle</button>
    <button data-f="status:echt">Echte Runs</button>
    <button data-f="status:fehltrigger">Fehltrigger</button>
    <button data-f="trades:ja">Mit Trades</button>
    <button data-f="profil:allin_july10">All-In july-10</button>
    <button data-f="profil:allin_july3">All-In july-3</button>
    <button data-f="profil:jre_july6">JRE</button>
    <button data-f="profil:mrbeast_next">MrBeast</button>
  </div>
  {''.join(karten)}
  <p class="fuss">Erzeugt {erzeugt} · Regenerieren: python -m operations.pipeline.dashboard ·
  Quellen: bot_events.jsonl, decisions_log.jsonl, run_annotationen.json, Gamma-Aufloesungen live</p>
</div>
<script>
  const knoepfe = document.querySelectorAll('#filter button');
  knoepfe.forEach(k => k.addEventListener('click', () => {{
    knoepfe.forEach(x => x.classList.remove('aktiv'));
    k.classList.add('aktiv');
    const f = k.dataset.f;
    document.querySelectorAll('.run').forEach(r => {{
      if (f === 'alle') {{ r.style.display = ''; return; }}
      const [art, wert] = f.split(':');
      r.style.display = (r.dataset[art] === wert) ? '' : 'none';
    }});
  }}));
</script>"""

    AUSGABE.write_text(seite, encoding="utf-8")
    print(f"Runs: {len(runs)} | Fills: {n_fills} | realisierte PnL: {summe_pnl:+.2f}")
    print(f"Geschrieben: {AUSGABE}")


if __name__ == "__main__":
    main()
