# Overleaf-Grundgeruest — Bachelorarbeit

LaTeX-Projekt fuer die Thesis. Kompiliert mit **pdfLaTeX + BibTeX**.

## Struktur

```
thesis/
  main.tex            Praeambel, Titelseite, bindet alle Kapitel ein
  references.bib      Kern-Literatur (Schluessel = source_id)
  chapters/
    01_einleitung.tex   Stub (Outline)
    02_theorie.tex      Stub (Outline, source_review_needed)
    03_methodik.tex     Inhalt (bounded-draft-ready)
    04_h1.tex           Inhalt (Ergebnis H1)
    05_h2.tex           Inhalt (Ergebnis H2)
    06_h3.tex           Inhalt (Ergebnis H3)
    07_erweiterungen.tex Monitor, Swiss, Praxisbeitrag
    08_diskussion.tex   Stub (Outline)
    09_ausblick.tex     Stub (Agenten-Pipeline, guarded)
  figures/            PNGs (F1-F3 hierher kopiert)
```

## Nach Overleaf bringen

1. Ordner `thesis/` als ZIP in ein neues Overleaf-Projekt hochladen.
2. Compiler auf **pdfLaTeX** stellen (Menu -> Settings).
3. Reihenfolge bei Bibliografie: pdfLaTeX -> BibTeX -> pdfLaTeX -> pdfLaTeX
   (Overleaf macht das automatisch beim erneuten Kompilieren).

## Figuren

Die Ergebnis-PNGs liegen im Projekt unter `figures/` und stammen aus
`data/results/`. Weitere Figuren bei Bedarf von dort nach `figures/` kopieren und
mit `\includegraphics{dateiname.png}` einbinden.

## Zitierschluessel

Die `\citep{...}`-Schluessel entsprechen den `source_id` aus
`data/literature/literature_index.csv`. Vor Abgabe durch die Better-BibTeX-Keys
ersetzen. Quellen mit Status `skimmed`/`pending` sind Platzhalter und erst nach
manuellem Review final zitierbar (siehe `docs/project/SOURCE_REVIEW_PACK.md`).
`zotero_poly_004` ist `rejected` und darf nicht zitiert werden.

## Status

Kapitel 3--7 sind bounded-draft-ready mit echten, gegen Artefakte gepruefen
Zahlen. Kapitel 1, 2, 8, 9 sind Outlines. Kein Kapitel ist final-submission-ready,
solange das manuelle Quellen-Review offen ist. Schweizer Orthografie: ss statt
scharfem s.
