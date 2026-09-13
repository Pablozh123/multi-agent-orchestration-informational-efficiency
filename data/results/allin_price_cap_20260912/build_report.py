"""Render the saved deterministic audit; no network or trading runtime imports."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
data = json.loads((HERE/'audit.json').read_text(encoding='utf-8'))
runs = {r['run']: r for r in data['runs']}
latest = runs['allin_september11']
primary = ['allin_july24', 'allin_july31', 'allin_august7', 'allin_september11']

def scenario(run, y, n):
    return next(s for s in run['scenarios'] if s['yes_cap'] == y and s['no_cap'] == n)

text = [
    '# All-In: Preisgrenzen rückblickend geprüft, 12. September 2026',
    '',
    'Befund: Die Preisgrenzen haben korrekte Käufe verhindert. Die Daten sprechen für einen gezielten Paper-Vergleich moderater Lockerungen. Sie rechtfertigen keine pauschale Erhöhung auf 98 oder 99 Cent.',
    '',
    '**Umfang und Quellen.** Neun All-In-Laufordner vom 3. Juli bis 11. September wurden inventarisiert. Primärer Vergleich: die sechs jüngsten Ordner. Davon vier mit passenden handelbaren Ereignissen: 24. Juli, 31. Juli, 7. August und 11. September. August 28 verarbeitete E287 gegen das August-21-Event. September 4 verarbeitete E289 gegen das alte September-4-Event. Beide ausgeschlossen. Ältere Läufe dienen nur als Fehlerkontext; insbesondere die mehrfachen Drops/Specials vom 10. Juli sind keine saubere Vergleichsstichprobe.',
    '',
    'Intendant Windows wurde für Status, Memory- und Agenda-Abgleich verwendet. Berechnungsquellen sind die lokalen Entscheidungslogs und damaligen Gamma-Snapshots unter `C:/Users/chole/ba-thesis/data/live`. Die öffentlichen Gamma-Auflösungen wurden für alle neun Event-Slugs erneut abgefragt. Ein SHA-256-Manifest aller Eingaben steht in `audit.json`. Kein Zugriff auf Trading-Zugangsdaten, keine Orders und keine Änderung der Limiten.',
    '',
    '**Letzte Nacht, E289.** Im Entscheidungslog steht ein realer AI-Fill über 3.75 USD / 4.17 Shares. Der Schlusszähler `ausgegeben_usd: 0.0` widerspricht dem Fill-Log und ist keine verlässliche Nullhandel-Aussage. Die übrigen sieben hier genannten Signale wurden allein durch die Preisprüfung blockiert. Alle acht Seiten stimmen mit der inzwischen finalen Marktauflösung überein.',
    '',
    'Jeweils die erste sichtbare zusätzliche Preisstufe oberhalb von YES 90 / NO 80. Die Beträge sind angezeigte Notional-Tiefe, keine bestätigten hypothetischen Fills. AI ist ein Zusatz zum bereits protokollierten Kauf.',
    '',
    '| Markt | Seite | Preis | Sichtbarer Einsatz USD | Gewinn bei Auflösung, Gebührenmodell USD |',
    '|---|---|---:|---:|---:|',
]
for c in latest['candidates']:
    base = .9 if c['side'] == 'YES' else .8
    above = [a for a in c['asks'] if base < float(a['price']) <= .99]
    if not above:
        continue
    a = min(above, key=lambda a: float(a['price']))
    p, q = float(a['price']), float(a['size'])
    net = q*(1-p)-q*c['rate']*p*(1-p)
    text.append(f"| {c['label']} | {c['side']} | {100*p:g} ct | {p*q:.2f} | {net:.2f} |")
text += [
    '',
    '**E289: ganze gespeicherte Bücher, 740 USD gemeinsames Szenariobudget.** Einmaliger Kaufversuch je Markt/Seite in protokollierter Reihenfolge. Gebührenäquivalent im Budget enthalten. NO bleibt in dieser Tabelle bei 80 Cent. Der Gewinn ist bereits aufgelöstes Szenarioergebnis, keine erwartete Rendite für nächste Woche.',
    '',
    '| YES-Limit | Gesamter Kapitaleinsatz inkl. Gebühren USD | Modellgewinn USD | Mehrgewinn gegenüber 90/80 USD |',
    '|---:|---:|---:|---:|',
]
baseline = latest['scenarios'][0]
for cap in (.9, .95, .97, .98, .99):
    s = scenario(latest, cap, .8)
    text.append(f"| {cap*100:g} ct | {s['cash']:.2f} | {s['pnl_model']:.2f} | {s['pnl_model']-baseline['pnl_model']:.2f} |")
text += [
    '',
    'YES 95 öffnet AI zu 93 und Google zu 94 Cent. YES 97 ergänzt kleine Anthropic-/IPO-Stufen und mehr AI. NO 90 oder 95 hätte letzte Nacht keinen zusätzlichen Kauf geöffnet. Erst NO 97 hätte Zuckerberg/Microsoft geöffnet: zusammen 22.32 USD sichtbares Notional und rund 0.66 USD Gewinn im Gebührenmodell. Smartphone zu 99 Cent hätte 69.03 USD gebunden, für rund 0.67 USD Gewinn.',
    '',
    '**Konkrete ältere Gelegenheiten.** Am 24. Juli waren Alignment NO zu 83 Cent mit 48.80 USD und Canada NO zu 84 Cent mit 125.87 USD in der ersten Stufe sichtbar; beide lösten richtig auf. Ein NO-Limit von 90 hätte diese eröffnet. Am 7. August waren IPO YES zu 97 Cent mit 119.12 USD und Stock Market NO zu 96 Cent mit 194.75 USD sichtbar. Mit dem heutigen Gebührenmodell ergeben diese ersten Stufen 3.54 beziehungsweise 7.80 USD Gewinn. Das ist eine Gebührensensitivität, weil die älteren Eingangssnapshots keine damaligen Gebührensätze enthalten.',
    '',
    '**Gegenbeispiele müssen mitgezählt werden.** Am 31. Juli war Red YES bei 98 Cent ein falsches Signal. Bei YES 98 / NO 80 ergäben die ersten Bücher zusammen 102.98 USD Einsatz und -2.98 USD Ergebnis; bei YES 99 / NO 80 437.89 USD und -18.02 USD. Neun der zehn protokollierten YES-Signale dieses Laufs waren richtig, trotzdem verliert das 99-Cent-Szenario. Am 24. Juli wurde Innovation NO real mit 20.86 USD gekauft und verlor. Schon unterhalb von 80 Cent existieren ASR-Fehler; höhere NO-Sweeps würden dieselben Fehlerpositionen vergrössern. Am 17. Juli dokumentiert das Fill-Log zusätzlich Tension NO über 22.50 USD, ebenfalls verloren.',
    '',
    '**Andere Schutzprüfungen.** E289 Nvidia: erster Zähler 0, Konsensdurchgang meldete eine Erwähnung. NO wurde deshalb durch den Endstand blockiert; der Markt löste YES auf. SpaceX NO war durch das Basisraten-Veto blockiert, obwohl die Auflösung NO war. Keiner dieser beiden Fälle ist eine reine Preislimit-Gelegenheit. Eine Änderung der Preisgrenze allein hätte diese Entscheidungen nicht verändert.',
    '',
    '**Normierter Vergleich zur Budgetverdrängung.** Die folgenden Differenzen verwenden absichtlich einheitlich 740 USD pro Lauf, unabhängig vom damaligen Kontostand und Profilbudget. Sie sind kein historischer PnL-Backtest. Höhere frühe YES-Sweeps können Budget für spätere günstigere NOs verbrauchen.',
    '',
    '| Lauf | Mehrgewinn YES 95 / NO 80 | YES 97 / NO 80 | YES 99 / NO 80 |',
    '|---|---:|---:|---:|',
]
for name in primary:
    r = runs[name]; b = r['scenarios'][0]['pnl_model']
    ds = [scenario(r, c, .8)['pnl_model']-b for c in (.95,.97,.99)]
    text.append(f"| {name} | {ds[0]:+.2f} | {ds[1]:+.2f} | {ds[2]:+.2f} |")
text += [
    '',
    '**Methodik und Grenzen.** Die Auflösung dient nur der Bewertung. Kandidaten werden aus YES/NO-Aktionen oder expliziten `yes_ask > cap` / `no_ask > cap`-Gründen bestimmt; Veto-, Zähler- und fehlende-Buch-Fälle bleiben ausgeschlossen. Pro Lauf, Markt und Seite wird die erste geeignete Entscheidung verwendet. Wiederholte Snapshots werden nicht als neue Liquidität addiert. Das reproduziert weder spätere Nachläufe noch historisch wechselnde Ausführungslogik. Im Hauptvergleich enthält kein ausgewähltes Buch zehn Stufen, und die gespeicherten besten Asks stimmen mit den Preisblockaden überein. Der Logger beschränkt trotzdem grundsätzlich auf zehn unsortierte Eingangsstufen; ältere Bücher können abgeschnitten sein. Die CSV enthält nur Bestpreise, keine Tiefe. Quote-Bestand bis zur Orderankunft, Netzwerkverzug, Mindestorder, Rundungen, Refreshes, konkurrierende Käufer und Wallet-Sharing sind nicht rekonstruiert. Die Darstellung ist sichtbare Liquidität bei der Entscheidung, keine garantierte Ausführbarkeit. Eine veränderte Grenze könnte zudem die Vorscan-Pause und damit Signal-/Abrufzeiten verändern. Diese zeitliche Rückwirkung wird nicht modelliert.',
    '',
    'Gebührenmodell: `Shares × rate × Preis × (1−Preis)` als USDC-Äquivalent. E289 belegt `rate=0.04`, `exponent=1` und aktivierte Gebühren im damaligen Snapshot. Für ältere Läufe wird derselbe heutige Satz nur als Sensitivität verwendet. Per-Fill-Rundung, mögliche Gebührenabzüge in Shares und Rebates sind nicht rekonstruiert. Quelle: [offizielle Polymarket-Gebühren](https://docs.polymarket.com/trading/fees), abgerufen am 12. September 2026.',
    '',
    '**Einordnung.** YES 90 ist für gut bestätigte Treffer teilweise zu streng. Ein Paper-Vergleich von YES 95 und NO 90 ist durch konkrete Fälle begründet. NO 90 hilft im Juli-Beispiel, in der letzten Nacht nicht. 97 Cent allenfalls als separat zu prüfende Ausnahme mit stärkerer Signalbestätigung; keine pauschale 98-/99-Cent-Freigabe aus dieser kleinen Stichprobe. Bei 97 Cent braucht das Gebührenmodell mehr als 97.1164 Prozent Trefferquote; bei 99 Cent mehr als 99.0396 Prozent. Vier Wochen, verwandte Wörter und gemeinsame ASR-Fehler liefern keine unabhängige Kalibrierung dieser Genauigkeit.',
    '',
    '**Reproduktion.**',
    '',
    '```powershell',
    'python -m operations.analysis.allin_price_cap_audit --live-root C:/Users/chole/ba-thesis/data/live --resolutions data/results/allin_price_cap_20260912 --output data/results/allin_price_cap_20260912/audit.json',
    'python data/results/allin_price_cap_20260912/build_report.py',
    'python -m pytest tests/test_allin_price_cap_audit.py -q',
    '```',
]
(ROOT/'docs/project/ALLIN_PRICE_CAP_AUDIT_2026-09-12.md').write_text('\n'.join(text)+'\n', encoding='utf-8')

plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), layout='constrained')
caps = [.9,.95,.97,.98,.99]
values = [scenario(latest, cap, .8) for cap in caps]
x = list(range(len(caps)))
axes[0].bar(x, [s['cash'] for s in values], color='#5a7892')
axes[0].set_xticks(x, [f'{cap*100:g} ct' for cap in caps])
axes[0].set_ylabel('Kapitaleinsatz inkl. Gebührenmodell (USD)')
axes[0].set_title('E289: mehr Kapital für kleine Zusatzgewinne')
axes[0].set_xlabel('YES-Limit, NO bleibt bei 80 ct')
for i,s in enumerate(values):
    axes[0].text(i,s['cash']+9,f"Gewinn\n{s['pnl_model']:.2f} $",ha='center',fontsize=9)
axes[0].set_ylim(0,660)
colors = ['#357a72','#d68232','#a64350']
for j,cap in enumerate([.95,.97,.99]):
    ys = [scenario(runs[name],cap,.8)['pnl_model']-runs[name]['scenarios'][0]['pnl_model'] for name in primary]
    axes[1].bar([i+(j-1)*.23 for i in range(4)],ys,width=.22,label=f'YES {cap*100:g} ct',color=colors[j])
axes[1].axhline(0,color='#444444',linewidth=.8)
axes[1].set_xticks(range(4),['24. Juli','31. Juli','7. Aug.','11. Sept.'])
axes[1].set_ylabel('Mehrgewinn gegenüber 90/80 (USD)')
axes[1].set_title('99 ct: Fehler und Budgetverdrängung')
axes[1].legend(frameon=False,fontsize=9)
fig.suptitle('Historische Buchszenarien, keine garantierten Fills\n740 USD je Lauf, erste Signalbücher; 4%-Gebührenmodell, ältere Gebühren unbestätigt',fontweight='bold',fontsize=12)
fig.savefig(HERE/'price_caps.png',dpi=160)
print(ROOT/'docs/project/ALLIN_PRICE_CAP_AUDIT_2026-09-12.md')
