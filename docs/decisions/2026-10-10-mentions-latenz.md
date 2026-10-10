# Mentions: frühe Teilergebnisse und unabhängige Marktdaten

Status: umgesetzt und offline geprüft. Kein Bot gestartet, keine Order gesendet.

## Auftrag und Entscheid

Chole autorisierte am 10.10.2026 frühere Treffer, unabhängige Quellenabfragen,
Entkopplung der Orderbücher und einen CPU/GPU-Vergleich. Im Nachauftrag wurden
auch inkrementelle MP3-Dekodierung und parallele Wallet-Sweeps ausdrücklich
beauftragt. Jev bleibt offen.

Während eines wachsenden MP3-Downloads bleiben die bisherigen 20-s-Abschnitte
mit 2 s Überlappung erhalten. Bei abgeschlossenem Download verwendet All-In
für einen grossen Rest weiterhin GPU-Batching, gibt aber jedes fertige
ASR-Segment sofort an Zähler und Entscheidung weiter. Der bisherige Aufruf
sammelte sämtliche Segmente zuerst in einer Liste. Das verzögerte alle Treffer
bis zum Ende des ASR-Durchlaufs.

Die Änderung ist ein explizites `inkrementell_final=True` im All-In-Bot.
Earnings und der YouTube-Probelauf behalten ihren vollständigen finalen Flush.
Der Transkriptionsfortschritt wird erst nach erfolgreicher ASR und
Sprecherprüfung fortgeschrieben. Ein Fehler überspringt keinen offenen Rest.

Durchgehend einzelne 20-s-Aufträge wurden als Standard verworfen: Im E292-Test
lieferten sie das erste Segment nach 0,66 s, brauchten insgesamt 152,34 s statt
44,51 s und verpassten einen Zuckerberg-Treffer. Kleine Aufträge minimieren
die erste Antwort, verschlechtern hier aber Durchsatz und einzelne Wortfunde.
Der gewählte Pfad erhielt in diesem Replay alle 13 bisherigen Markt-Zählwerte.
Das belegt keine vollständige Transkriptionsrichtigkeit.

## Quellen und Bücher

Prober, RSS und YouTube erhalten unabhängige Hintergrundabfragen mit je einem
Ergebnisplatz. Der Hauptpfad prüft vorhandene Ergebnisse alle 0,1 s. Langsame
Netzwerkzugriffe auf Ersatzquellen halten ihn nicht auf. Nach erkanntem Drop
stoppen weitere Abfragen. RSS/YouTube bleiben wegen Quellenabweichungen erhalten,
insbesondere dem früher dokumentierten E288-Dateinamen `E288_AUDIO_v102.mp3`.
YouTube bleibt eine langsamere Ersatzquelle, kein gleich schneller MP3-Pfad.

Ein öffentlicher CLOB-Markt-WebSocket lädt die vollständigen Token-Bücher vor
dem Drop und pflegt Preisänderungen im Speicher. Audioverarbeitung und
Buchlogger verwenden diesen Speicher statt synchroner REST-Buchabfragen.
Initialsnapshot, gültige Preise/Grössen, Heartbeat und verbundener Zustand sind
Voraussetzung. Bei Unterbruch werden Bücher verworfen; ein Reconnect braucht
neue Snapshots. Fehlende Bücher blockieren keine Audioauswertung und erlauben
keine Order. Der Nachlauf wartet bei offenen Kandidaten auf die Verbindung.

Der LiveExecutor bereitet über die öffentliche SDK-Methode `get_fee_exponent`
Token-, Tick-, Fee- und Neg-Risk-Kontext vor. Ein öffentlicher `/version`-Abruf
beim ersten Orderaufbau bleibt: Die öffentliche `get_version`-Methode befüllt
den privaten SDK-Versionscache nicht. Kein Eingriff in private SDK-Felder.

Preisdeckel, Wortpuffer, STOP, NO-Konsens und Gap-Verify bleiben erhalten.
Im Live-All-In-Pfad ersetzt gemäss Nachauftrag das Wallet den festen
Gesamtbetrag. Andere Serien und simulierte Budgets behalten ihren Standard.

## Nachauftrag: MP3 und Orders

Ein fortlaufender PyAV-Decoder liest komprimierte MP3-Bytes nur einmal und
liefert stabile Samples. Temporäres EOF bleibt offen; finales EOF leert Codec
und Resampler, bevor die Episode als vollständig gilt. Die bestehende
Abhängigkeit PyAV genügt, kein zusätzliches Modell oder Paket. Bei E292
zehn wachsende Dateistände 58,97 zu 8,98 s, fertiges Audio bitgleich.

Unabhängige Thread-Aufträge pro Markt entkoppeln Orders von der Audioauswertung.
Ein gemeinsames Wallet-Ledger reserviert jede Portion vor POST und rechnet
bestätigte Fills ab. Vorhandener 3-%-Puffer, Portionengrösse und Preisdeckel
gelten weiter. Positive Fills führen zu weiteren Portionen, bis ausführbare
Liquidität oder Budget endet. Andere Wörter können währenddessen bestellen.
Ein verzögerter Clip wird nach Bestätigung zum verbleibenden Sweep fortgesetzt.

Unklare POSTs behalten Mittel und Marktsperre. Bestätigungen laufen separat
mit 0,1-s-Pollabstand, Wallet-Abfragen höchstens alle 5 s. Alte Balancewerte
können bestätigte Ausgaben nicht rückgängig machen. Einzahlungen vor dem
ersten Trade sind möglich; danach bleibt die Balance konservativ monoton.
Keine prozessübergreifende Reservierung und keine vollständige Recovery
unbekannter Order-IDs über Neustarts. Netzwerkfehler werden nicht blind wiederholt.

FAK und verzögerte Status sind in der offiziellen
[Polymarket-Orderdokumentation](https://docs.polymarket.com/concepts/order-lifecycle)
beschrieben. Der SDK-Transport nutzt einen gemeinsamen HTTPX-Client, dessen
[offizielle API](https://www.python-httpx.org/api/) Thread-Nutzung unterstützt.
Die tatsächliche SDK-Integration wurde zusätzlich mit getrennten Orderargumenten
und vorbereiteten Token-Caches geprüft. Orders selbst wurden nur gemockt.

## Folgen und Grenzen

Frühe YES-Treffer müssen nicht mehr auf den kompletten finalen ASR-Rest warten.
Späte Schwellen können weiterhin fast den ganzen Durchlauf brauchen. NO wartet
weiter auf vollständiges Audio, den Konsensdurchlauf und Gap-Verify.

CPU/GPU laufen auf dieser Maschine gleichzeitig. Im begrenzten 360-s-Test
brauchten beide Prüfungen parallel 66,15 s statt seriell 89,64 s. CPU-small
allein brauchte seriell 80,22 s, GPU-large 9,41 s. Modellzählungen unterschieden
sich. Ein Produktionsumbau wurde daraus nicht abgeleitet: Der Test ist keine
vollständige, inhaltlich validierte NO-Prüfung.

Messungen, Reproduktion, offene Punkte und Prüfresultate stehen im
[Umsetzungsbericht](../project/MENTIONS_OPTIMIERUNG_2026-10-10.md).
