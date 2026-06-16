# Blueprint: laufendes Multiagenten-Werkzeug (Anomalie-Monitor)

Idee: ein laufendes Tool (Website-Terminal), das Polymarket-Maerkte scannt,
Anomalien erkennt, Faelle aufbereitet und priorisierte Pruef-Empfehlungen liefert.
Mehrere Agenten arbeiten zusammen. Menschliche Kontrolle bleibt im Loop.

## Die entscheidende Grenze: Produkt vs Thesis
- THESIS: alle empirischen Aussagen (H1-H3, Signatur) kommen NUR aus dem
  deterministischen, getesteten Python-Kern. Das Agenten-Tool ist dort
  dokumentierter Praxis-/Prozessbeitrag, nie Beweisquelle. So bleibt die Arbeit
  verteidigbar.
- PRODUKT (Website): darf den vollen Agenten-Loop live fahren. Mehr Spielraum,
  aber weiterhin read-only, kein autonomer Handel, keine personalisierte
  Anlageberatung. "Empfiehlt Handlungen" heisst hier: priorisierte
  PRUEF-Empfehlungen (beobachten, Quelle pruefen, eskalieren), nicht Kauf/Verkauf.

## Architektur in vier Schichten
0. Deterministischer Kern (Python, Thesis-Repo, read-only):
   pull public Polymarket-Daten (Gamma/CLOB/Data, read-only), berechnet
   Markt-z, Wallet-Tier-z, Konzentration/HHI, die Informed-Trading-Signatur und
   matcht Ereigniskandidaten. Schreibt bounded Artefakte (Review-Queue,
   Case-Packets). Rechnet ALLE Kennzahlen. Keine Order-/Trading-Pfade.
1. MCP-Lese-Schicht (bounded): genau der dokumentierte Vertrag --
   get_anomaly_review_summary, get_anomaly_case, list_monitor_artifacts,
   get_method_limits. Max 50 Zeilen, kein rohes SQL, keine Wallet-Adressen
   default, llm_audit_log Pflicht. Agenten sehen nur Zusammenfassungen.
2. Agenten (die "verschiedenen Agenten"):
   - EventScout: sammelt belegte Ereigniskandidaten (Quelle, Zeitstempel) und
     mappt sie auf Maerkte.
   - CaseNarrative: schreibt aus der bounded Zusammenfassung einen lesbaren Fall.
   - SkepticReviewer: prueft adversarial gegen (Aufmerksamkeitsevent, neue
     Nutzer, beidseitiger Fluss) und stuft schwache Faelle ab.
   - Orchestrator: gewichtet Signale + Skeptiker, rankt Faelle in eine
     priorisierte Pruef-Queue mit Pruef-Empfehlung (beobachten/pruefen/eskalieren).
   Agenten interpretieren und schlagen vor. Python entscheidet die Zahlen. Jeder
   LLM-Call wird protokolliert.
3. Website-UI (Produkt): Live-Scan, priorisierte Anomalie-Queue, Fall-Narrative,
   Skeptiker-Notiz, Signal-Charts. Mensch prueft und entscheidet. Kein
   Auto-Trading, keine Finanzberatung.

## Bau-Reihenfolge
Stufe 1 (Thesis-Repo, deterministisch): Informed-Trading-Signatur als getestetes
   Modul (siehe NEXT_GOAL_informed_trading_signature.md) und die Review-Queue
   replay-first live-faehig machen. -> schaltet die Datenbasis frei.
Stufe 2 (Thesis-Repo): MCP-Lese-Schicht ueber die bounded Artefakte bauen
   (4 Tools, Audit-Log, 50-Zeilen-Cap). Erste echte Agenten-Aktivierung, aber nur
   ueber Zusammenfassungen. Jetzt erlaubt, weil der Kern steht.
Stufe 3 (Website-Repo): die 4 Agenten ueber die MCP-Tools verdrahten und die
   priorisierte Queue im UI zeigen.

## Codex-Starter fuer Stufe 2 (nach Stufe 1)
Lies AGENTS.md, ARCHITECTURE_DECISIONS.md (21, 22) und die future_mcp_contract in
data/results/monitor_anomaly_review_metadata.json. Setze ein Goal
goal-monitor-mcp-readonly-001. Baue operations/mcp/ als read-only MCP-Server mit
genau vier Tools (get_anomaly_review_summary, get_anomaly_case,
list_monitor_artifacts, get_method_limits), max 50 Zeilen je Antwort, kein rohes
SQL, keine Wallet-Adressen default, jede Anfrage in llm_audit_log. Nur Lesen aus
bestehenden bounded Artefakten. Tests fuer Row-Cap, Adress-Guard, Audit-Log.
Atomarer Commit, dann update_status, WORK_LOG, review_check, commit_plan.

## Was bewusst draussen bleibt
Autonomer Handel, Order-Ausfuehrung, personalisierte Anlageberatung,
Profitabilitaetsversprechen, agentenberechnete Kennzahlen, Wallet-Adress-Ausgabe.
