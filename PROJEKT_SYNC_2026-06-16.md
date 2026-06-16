# Projekt-Synchronisation — Standortbestimmung

Datum: 2026-06-16
Zweck: Faden wieder aufnehmen. Wo steht die BA, was fehlt, wie weiter — im Rahmen.

---

## 1. Kernbefund: zwei Projekte, nicht eins

| Projekt | Ort | Was es ist | BA-Status |
| --- | --- | --- | --- |
| **Thesis** | `ba-thesis/` (dieses Repo) | Empirische Effizienzanalyse Polymarket vs. traditionelle Quellen | Empirie fertig, Text offen |
| **Website** | `Projects/prediction-market-terminal` (separates GitHub-Repo) | Streamlit-Tool: predictparity-Klon + Paper-Copytrading, ~10k Zeilen, 14 Seiten | Eigenstaendiges Tool, **nicht** Teil des Thesis-Repos |

Das «Faden verloren»-Gefuehl kommt daher: die letzten Arbeitssessions liefen fast nur ueber **Website-Infrastruktur** (git-Recovery, Copytrading-Spec, CI). Die eigentliche Thesis-Analyse und das Schreiben wurden wiederholt vertagt.

---

## 2. Was die Thesis schon hat (stark)

- **Deterministischer Python-Kern, 640 Tests gruen** (`pytest`, Stand STATUS.md).
- **H1** Forecast-Qualitaet (Brier vs. 538/Umfragen, inkl. Diebold-Mariano, Kalibrierung) — real gerechnet, ~158 Artefakte.
- **H2** Event-Window-Reaktion um kuratierte Ereignisse — gerechnet.
- **H3** Wallet-Tier-Timing + Granger (ohne Kausalanspruch) — gerechnet.
- **Swiss-Referendum** als aktueller Side-Track: Polymarket vs. SRG/gfs.bern, Tamedia, YouGov.
- Insgesamt **~387 Artefakte** (CSV/JSON/PNG/HTML) in `data/results/`, **43 Figuren**.
- **Dozentenbericht fertig**, jede Aussage auf ein deterministisches Artefakt gemappt.

Fazit: Der wissenschaftliche Beitrag (die Empirie) ist im Grunde **da**. Das ist mehr, als es sich gerade anfuehlt.

---

## 3. Was wirklich fehlt

1. **Der geschriebene Thesis-Text** — kritischer Pfad. 23 Source-Review-Zeilen offen, H1–H3-Prosa «draft-ready» aber 0 final, kein Overleaf-Export.
2. **RCP-Wahrscheinlichkeits-Transformation** noch nicht dokumentiert — blockt einen H1-Vergleich (per Architektur-Regel 8).
3. **Website-Entscheidung** — gehoert das Terminal in die BA (als zitierbares Monitor-/Daten-Tool) oder bleibt es Nebenprojekt? Bisher nie grundsaetzlich geklaert.
4. **Die Agenten-Pipeline** — siehe Abschnitt 4.
5. Offene Tech-Limitation: H3-Wallet-Daten aktuell BUY-only / Filter >= 10'000 USD (in STATUS.md als Limitation vermerkt).

---

## 4. Die Agenten-Pipeline richtig einordnen

Das urspruengliche Ziel «Multiagenten-Pipeline» ist **nicht verschwunden — es ist bewusst geparkt.**

- `AGENTS.md` und `ARCHITECTURE_DECISIONS.md` (Regel 1, 14) sperren Agenten, **bis der deterministische Kern steht**. Aktiv sind sie nur als Guard-Stubs (`raise RuntimeError("Deferred until deterministic analysis core is complete")`).
- Die **echte Implementierung liegt schon fertig** in `legacy/deferred_agents/` (Orchestrator ~252 Z. + market/whale/sentiment) und `legacy/deferred_mcp/`.
- **Das Gate ist jetzt offen**: Kern steht, Tests gruen, Baseline dokumentiert. Reaktivieren ist also scope-konform.

Wichtig — was die Pipeline laut deinen eigenen Regeln sein **darf** und was nicht:

- ✅ Liest nur **bounded, vorab berechnete Summaries** (H1/H2/H3).
- ✅ **Interpretiert** strukturiert, loggt jeden Call in `llm_audit_log`.
- ❌ Rechnet **keine** Metriken (Brier, CAR, Granger, Tiers) — das bleibt Python.

Damit ist sie **kein grosses neues System**, sondern 1–2 fokussierte Module. Die Skill `thesis-architect-setup` ist genau dafuer da. Sie ist das Sahnehaeubchen (Innovations-Bonus), nicht das Fundament — die Note kommt aus dem Text.

---

## 5. Priorisierter Fahrplan (im Rahmen)

| # | Schritt | Warum zuerst | Aufwand |
| --- | --- | --- | --- |
| 1 | **Website-Rolle entscheiden + schriftlich abgrenzen** | Sonst frisst sie weiter Zeit; blockiert Klarheit | ~30 Min |
| 2 | **RCP-Transformation dokumentieren** | Kleiner Block, schaltet H1-Vergleich frei | 0.5 Tag |
| 3 | **Thesis-Text schreiben** (Intro → Methodik → H1/H2/H3 → Swiss → Diskussion) | Kritischer Pfad zur Abgabe, Empirie ist da | Hauptarbeit |
| 4 | **Bounded Interpretations-Pipeline** aus `legacy/` reaktivieren | «Macht etwas», scope-konform, als Innovations-Kapitel | 1–2 Tage |

Reihenfolge bewusst: **erst fertig schreiben, was die Note traegt — dann die Pipeline als Bonus.**

---

## 6. Offene Entscheidungen (brauchen dich)

- Gehoert das `prediction-market-terminal` in die BA? Wenn ja, in welcher Rolle (Datenquelle / Monitor-Kapitel / Demo)?
- Soll die Agenten-Pipeline ein eigenes Thesis-Kapitel werden oder nur ein dokumentierter Ausblick bleiben?
- Abgabetermin als fixe Leitplanke setzen (Mitte August laut Projektgedaechtnis) — danach Fahrplan takten.
