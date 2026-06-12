from __future__ import annotations

from html.parser import HTMLParser
from zipfile import ZipFile

from operations.project.build_dozenten_report import build_report


class _ImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.images: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "img":
            return
        attr_map = dict(attrs)
        src = attr_map.get("src")
        if src:
            self.images.append(src)


def test_build_dozenten_report_outputs_readable_artifacts(tmp_path):
    output_dir = tmp_path / "report"
    result = build_report(
        markdown_output=output_dir / "report.md",
        html_output=output_dir / "report.html",
        docx_output=output_dir / "report.docx",
        asset_dir=output_dir / "assets",
    )

    markdown_path = output_dir / "report.md"
    html_path = output_dir / "report.html"
    docx_path = output_dir / "report.docx"
    overview_path = output_dir / "assets" / "project_pipeline_overview.png"

    assert result["figure_count"] >= 4
    assert markdown_path.exists()
    assert html_path.exists()
    assert docx_path.exists()
    assert overview_path.exists()

    html_text = html_path.read_text(encoding="utf-8")
    assert "Highlevel-Projektstand" in html_text
    assert "Review-Access bleibt pausiert" in html_text
    assert "Phase 12: Thesis Consolidation And Evidence Mapping" in html_text
    assert "5 Kern-Tabellen" in html_text
    assert "4 Kern-Figuren" in html_text
    assert "thesis_table_figure_captions.csv" in html_text
    assert "Projektmatrix fuer die naechste Abstimmung" in html_text
    assert "Monitor Review-Access" in html_text
    assert "Review-Access bleibt pausiert" in html_text
    assert "Agenten bleiben Dokumentationsausblick" in html_text
    assert "llm_audit_log" in html_text
    assert "Naechste Arbeitsschritte" in html_text
    assert "work_01_source_review" in html_text
    assert "work_10_final_qa" in html_text
    assert "Kapitelweise Umsetzungscheckliste" in html_text
    assert "exec_04_04_h1_results" in html_text
    assert "advisor_q06_swiss_gate" in html_text
    assert "Schreib- und Abnahmelogik fuer den naechsten Entwurf" in html_text
    assert "Quellenreview Kernquellen" in html_text
    assert "Source-Review-Worksheet enthaelt 15 manuelle Review-Zeilen" in html_text
    assert "11 Priority-1-Methodenquellen" in html_text
    assert "Alle Reviewer-Entscheide bleiben pending" in html_text
    assert "H1 - Forecast-Qualitaet" in html_text
    assert "H1 Forecast-Quality Vergleich" in html_text
    assert "h1_forecast_quality.png" in html_text
    assert "H1 Forecast-Quality Synthesis" in html_text
    assert "h1_forecast_quality_synthesis.png" in html_text
    assert "H1 Claim-Evidence Audit" in html_text
    assert "h1_claim_evidence_audit.png" in html_text
    assert "H1 Poll-Comparison Result" in html_text
    assert "h1_poll_comparison_result.png" in html_text
    assert "H1 Poll-Claim Readiness" in html_text
    assert "h1_poll_claim_readiness.png" in html_text
    assert "H1 Poll-Scope Frontier" in html_text
    assert "h1_poll_scope_frontier.png" in html_text
    assert "H1 Poll-Decision Matrix" in html_text
    assert "h1_poll_decision_matrix.png" in html_text
    assert "H1 Robust Poll-Scope Quality" in html_text
    assert "h1_robust_poll_scope_quality.png" in html_text
    assert "H1 Robust Poll-Scope Unit Quality" in html_text
    assert "h1_robust_poll_scope_unit_quality.png" in html_text
    assert "H1 Poll-Comparison Unit Robustness" in html_text
    assert "h1_poll_comparison_unit_robustness.png" in html_text
    assert "H1 Direct Poll Loss Decomposition" in html_text
    assert "h1_direct_poll_loss_decomposition.png" in html_text
    assert "H1 Direct Poll State-Cluster Diagnostic" in html_text
    assert "h1_direct_poll_state_cluster_diagnostic.png" in html_text
    assert "H1 Direct Poll Outlier Robustness" in html_text
    assert "h1_direct_poll_outlier_robustness.png" in html_text
    assert "h1_popular_vote.png" in html_text
    assert "H1 Calibration Diagnostic" in html_text
    assert "h1_calibration_diagnostic.png" in html_text
    assert "H1 Evidence-Scope Audit" in html_text
    assert "h1_evidence_scope.png" in html_text
    assert "H1 Expansion-Readiness Audit" in html_text
    assert "h1_expansion_readiness.png" in html_text
    assert "H1 Margin-Threshold Readiness" in html_text
    assert "h1_margin_threshold_readiness.png" in html_text
    assert "H1 Final-Snapshot Extension" in html_text
    assert "h1_final_snapshot.png" in html_text
    assert "H1 State-Poll-Snapshot Extension" in html_text
    assert "h1_state_poll_snapshot.png" in html_text
    assert "H1 270toWin Polling-Average Extension" in html_text
    assert "h1_270towin_poll_average.png" in html_text
    assert "H1 State-Date Poll Panel" in html_text
    assert "h1_state_poll_panel.png" in html_text
    assert "H1 State-Date Poll Panel Temporal Diagnostic" in html_text
    assert "h1_state_poll_panel_temporal_diagnostic.png" in html_text
    assert "H1 State-Date Poll Panel Horizon Diagnostic" in html_text
    assert "h1_state_poll_panel_horizon_diagnostic.png" in html_text
    assert "H1 &lt;=90-Day State-Level Support" in html_text
    assert "h1_state_poll_panel_horizon_state_support.png" in html_text
    assert "H1 &lt;=90-Day Score Quality" in html_text
    assert "h1_state_poll_panel_near_window_quality.png" in html_text
    assert "H1 Poll-Transform Sensitivity" in html_text
    assert "h1_state_poll_snapshot_sensitivity.png" in html_text
    assert "H1 State-Poll Coverage Audit" in html_text
    assert "h1_state_poll_snapshot_coverage.png" in html_text
    assert "H1 Rieke 50-State Forecast Extension" in html_text
    assert "h1_rieke_state_forecast.png" in html_text
    assert "H1 270toWin/JHK 50-State Forecast Extension" in html_text
    assert "h1_270towin_state_forecast.png" in html_text
    assert "H1 State-Source Consensus Diagnostic" in html_text
    assert "h1_state_source_consensus.png" in html_text
    assert "H1 Competitive-State Diagnostic" in html_text
    assert "h1_competitive_state_diagnostic.png" in html_text
    assert "H1 State-Date Competitiveness x Horizon" in html_text
    assert "h1_state_poll_panel_competitiveness.png" in html_text
    assert "H1 State-Level Significance Diagnostic" in html_text
    assert "h1_state_poll_panel_state_significance.png" in html_text
    assert "Final-Snapshot-Erweiterung" in html_text
    assert "5 von 8 geloesten 2024-Outcomes" in html_text
    assert "8 von 13 geloesten State-Outcomes" in html_text
    assert "43 gematchte State-Outcomes" in html_text
    assert "14 Faellen, poll-derived in 29" in html_text
    assert "Mean Brier 0.0304 vs 0.0416" in html_text
    assert "MAE 2.0 bis 10.0 Prozentpunkte" in html_text
    assert "Lower-Loss-Spanne 7 bis 12 von 13 State-Outcomes" in html_text
    assert "50 US-States geprueft" in html_text
    assert "50 mit Polymarket-State-Markt" in html_text
    assert "13 valide H1-Brier-Paare" in html_text
    assert "37 wegen fehlender 538-Snapshot-Pollwerte" in html_text
    assert "50 geloeste State-Outcomes gegen Rieke poll-based model" in html_text
    assert "Mean Brier 0.0262 vs 0.0296" in html_text
    assert "12 von 50" in html_text
    assert "38 von 50" in html_text
    assert "50 geloeste State-Outcomes gegen 270toWin/JHK" in html_text
    assert "22 exakt ausgewiesene Wahrscheinlichkeiten" in html_text
    assert "28 zensierte &gt;99.9-Prozent-Boundary-Werte" in html_text
    assert "Mean Brier 0.0262 vs 0.0306" in html_text
    assert "9 von 50" in html_text
    assert "40 von 50" in html_text
    assert "156 Source-State-Vergleiche" in html_text
    assert "All-Source-State-Konsens: Polymarket 9 States, Comparatoren 37" in html_text
    assert "Zwei direkte Poll-Transform-Quellen: Polymarket 8 von 13 States" in html_text
    assert "Polymarket 35 von 52 All-Source-Faellen" in html_text
    assert "18 von 19 direkten Poll-Transform-Faellen" in html_text
    assert "Polymarket 0 von 40, Comparatoren 40 von 40" in html_text
    assert "16 von 22 Audit-Zeilen" in html_text
    assert "12 von 15 stuetzend" in html_text
    assert "Primaerer &lt;=90-Tage-Low/Middle-Poll-Distanz-Scope" in html_text
    assert "Polymarket 262 von 285 State-Date-Zeilen" in html_text
    assert "State-Ebene Polymarket 9 von 9" in html_text
    assert "Vollpanel-Gegenbeleg poll-derived 1360 von 1720" in html_text
    assert "Status not_proven" in html_text
    assert "4 von 13 Claim-Zeilen stuetzen den bounded &lt;=90-Tage" in html_text
    assert "5 Gegenbeispiel-Scopes" in html_text
    assert "3 Mean-Loss-Stuetze-ohne-Mehrheit-Zeilen" in html_text
    assert "Polymarket 262 von 285 State-Date-Zeilen (91.9%)" in html_text
    assert "17 von 17 State-Month-Einheiten, exact p=7.6e-06" in html_text
    assert "Bounded Claim supported 1; breiter Claim belegt 0" in html_text
    assert "8 von 30 Horizont-x-Poll-Distanz-Scopes" in html_text
    assert "Groesster robuster Scope: <=120 days + Low/middle distance" in html_text
    assert "Polymarket 313 von 433 State-Date-Zeilen (72.3%)" in html_text
    assert "18 von 26 State-Month-Einheiten, exact p=0.0378" in html_text
    assert "Staerkster Scope lte_90_days_low_middle_distance: 285 Zeilen, p=7.6e-06" in html_text
    assert "&lt;=90 Tage alle Distanzen: Polymarket 262 von 357 Zeilen (73.4%)" in html_text
    assert "State-Month p=0.0758" in html_text
    assert "Vollpanel-Gegenbeleg poll-derived 1360 von 1720" in html_text
    assert "2 von 9 Entscheidungszeilen sind robuste bounded-Yes-Zeilen" in html_text
    assert "3 Mean-Loss-Stuetze-ohne-Mehrheit-Zeilen" in html_text
    assert "2 Gegenbelege bleiben als Grenzen" in html_text
    assert "Polymarket 313 von 433 State-Date-Zeilen (72.3%)" in html_text
    assert "1436 Forecast-Zeilen aus 718 State-Date-Faellen" in html_text
    assert "Mean Brier 0.1982 vs poll-derived 0.2555" in html_text
    assert "ECE 0.3868 vs 0.4251" in html_text
    assert "Polymarket 262 von 285 Zeilen (91.9%)" in html_text
    assert "alle Outcomes dort positiv, Separation nicht definiert" in html_text
    assert "Breiter Claim belegt 0" in html_text
    assert "8 Aggregationszeilen ueber robuste Poll-Scopes" in html_text
    assert "State-Month 18 von 26" in html_text
    assert "poll-derived 8, p=0.0378" in html_text
    assert "State-Month 17 von 17 (p=7.6e-06" in html_text
    assert "State-Horizon 17 von 17 (p=7.6e-06" in html_text
    assert "Medianer State-Month-Brier-Vorteil 0.0484" in html_text
    assert "0.0723 im staerksten Scope" in html_text
    assert "18 von 26 State-Month-Einheiten, p=0.0378" in html_text
    assert "Kalibrierungskontext: 5 von 5 Pairwise-Reihen" in html_text
    assert "2 von 5 auch per Fallmehrheit" in html_text
    assert "Bounded ready 1; breiter Claim 0; Status not_proven" in html_text
    assert "Primaerer Scope nach Aggregation" in html_text
    assert "17 von 17 State-Month-Einheiten" in html_text
    assert "17 von 17 State-Horizon-Einheiten" in html_text
    assert "State-Month exact p=7.6e-06" in html_text
    assert "95-Prozent-Untergrenze 0.838" in html_text
    assert "Full-Panel-State-Month-Gegenbeleg: poll-derived 61 von 80" in html_text
    assert "Late-High-Distance-State-Month-Gegenbeleg: poll-derived 8 von 8" in html_text
    assert "exact p=0.0039" in html_text
    assert "Direkte Poll-Transform-Vergleiche: Mean Brier Polymarket 0.0544 vs poll-derived 0.0729" in html_text
    assert "Polymarket niedrigerer Verlust in 22 von 56 Source-State-Faellen" in html_text
    assert "poll-derived in 34" in html_text
    assert "Total-Margin-Ratio 18.2" in html_text
    assert "State-Cluster-Diagnostik ueber 43 States" in html_text
    assert "gleichgewichteter mittlerer Verlustvorteil 0.0122" in html_text
    assert "Bootstrap-95%-Intervall 0.0041 bis 0.0217" in html_text
    assert "Sign-Flip-p=0.0045" in html_text
    assert "Polymarket 13 States, poll-derived 30" in html_text
    assert "Outlier-Diagnostik ueber 43 State-Cluster" in html_text
    assert "voller Mean 0.0122" in html_text
    assert "alle Leave-one-state-out Means positiv 1" in html_text
    assert "Minimum 0.0095 ohne Wisconsin" in html_text
    assert "bis 6 entfernte States positiv" in html_text
    assert "kippt bei 7 entfernten States auf -0.0001" in html_text
    assert "groesster positiver State Wisconsin (0.1248)" in html_text
    assert "Polymarket 262 von 285 State-Date-Zeilen" in html_text
    assert "9 von 9 States" in html_text
    assert "Binomial-p-Wert 0.0020" in html_text
    assert "95-Prozent-Untergrenze 0.717" in html_text
    assert "Polymarket 0 von 72" in html_text
    assert "poll-derived 72 von 72" in html_text
    assert "h1_reliability_curve.png" not in html_text
    assert "Polymarket niedrigerer Tagesverlust" in html_text
    assert "7 von 9 Vergleichszeilen stuetzen Polymarket im mittleren Brier" in html_text
    assert "3 von 9 zeigen eine Mehrheit niedrigerer Einzelfallverluste" in html_text
    assert "breiter Viele-Faelle-Beweis 0 von 9" in html_text
    assert "Popular-Vote-Erweiterung" in html_text
    assert "21 Zeilen, poll-derived in 30" in html_text
    assert "Mean Brier 0.5179 vs 0.4824" in html_text
    assert "Margin-Threshold-Readiness" in html_text
    assert "7 Trump-State-Margin-Maerkte geprueft" in html_text
    assert "0 neue H1-Brier-Faelle" in html_text
    assert "4 sind durch fehlende zeitliche Ueberlappung blockiert" in html_text
    assert "192 Forecast-Case-Zeilen" in html_text
    assert "aus 7 Quellen und 5 Pairwise-Reihen" in html_text
    assert "5 von 5 zeigen niedrigeren mittleren Polymarket-Brier" in html_text
    assert "2 von 5 auch eine Mehrheit niedrigerer Einzelfallverluste" in html_text
    assert "Forecast-Qualitaets-, aber kein klarer Kalibrierungssieg" in html_text
    assert "1720 gematchte State-Date-Zeilen" in html_text
    assert "Polymarket niedrigerer Verlust in 360 Zeilen" in html_text
    assert "poll-derived niedrigerer Verlust in 1360" in html_text
    assert "Mean Brier 0.1595 vs 0.1026" in html_text
    assert "Polymarket-stuetzende Monate 2024-08, 2024-09" in html_text
    assert "280 von 387 Zeilen" in html_text
    assert "poll-derived niedrigerer Verlust in 107" in html_text
    assert "Mean Brier 0.1842 vs 0.2543" in html_text
    assert "&lt;=90-Tage-Fenster" in html_text
    assert "262 von 357 Zeilen" in html_text
    assert "poll-derived niedrigerer Verlust in 95" in html_text
    assert "Mean Brier 0.1799 vs 0.2520" in html_text
    assert "Polymarket 8 von 13 States" in html_text
    assert "5 States stuetzen Polymarket nicht" in html_text
    assert "714 Forecast-Zeilen aus 357 State-Date-Faellen" in html_text
    assert "Fixed-Bin-ECE 0.3797 vs 0.4391" in html_text
    assert "Probability-Separation 0.4560 vs 0.4366" in html_text
    assert "Schweizer Referendum" in html_text

    parser = _ImageParser()
    parser.feed(html_text)
    assert len(parser.images) == result["figure_count"]
    assert all((html_path.parent / src).resolve().exists() for src in parser.images)

    with ZipFile(docx_path) as archive:
        media = [name for name in archive.namelist() if name.startswith("word/media/")]
    assert len(media) == result["figure_count"]
