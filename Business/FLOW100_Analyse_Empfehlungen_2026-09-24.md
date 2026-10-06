# FLOW100 – Analyse und nächste Geschäftshypothesen

Stand: 24.09.2026. Grundlage: die sieben vorhandenen Business-Dokumente und ergänzende Recherche anhand offizieller Dokumentation und Anbieterwebseiten. Dies ist eine strategische Einschätzung, keine validierte Umsatzprognose. Bestehende Dokumente bleiben als Entscheidungsverlauf erhalten.

## 1. Empfehlung

**Zuerst einen engen, wiederkehrenden Datenabgleich für Fachanwender testen. Den deutschen Register-Actor vorerst nicht nach der vorhandenen Bauspezifikation umsetzen.**

Mein Favorit: Lieferantenpreislisten vergleichen und einen nachvollziehbaren Änderungsbericht liefern. Alternativen: Importprüfung für genau ein Zielformat oder ein Ausschreibungsmonitor für genau eine Branche.

Die Empfehlung beruht auf deinem dokumentierten Profil: .NET, SQL, Schnittstellen und ERP-Prozesse; 5–10 Stunden pro Woche; weniger als CHF 1'000 Jahresbudget; kein Kaltvertrieb; zunächst lernen, später CHF 1'000–3'000 monatlich und ein übertragbares Produkt. Diese Angaben wurden aus deinen Notizen übernommen, nicht neu bestätigt. Offen bleibt insbesondere, ob dein Einkommensziel Umsatz oder verfügbaren Gewinn meint.

Wichtig: Keine der drei neuen Ideen hat bisher nachgewiesene Nachfrage für unser konkretes Angebot. Der Favorit ist die beste nächste Hypothese, noch kein Bauentscheid.

## 2. Was an den bisherigen Überlegungen gut ist

- Dein Fachwissen passt zu betrieblichen Aufgaben, bei denen fehlerhafte Daten Geld und Zeit kosten.
- Kleiner Umfang, überprüfbare Ergebnisse und transparente Fehlerbehandlung sind eine tragfähige Produktphilosophie.
- Der Fokus auf Self-Service berücksichtigt dein Zeitbudget.
- Die Dokumente korrigieren frühere Empfehlungen, sobald Gegenargumente auftauchen.
- Ein von der Plattform unabhängiger Produktkern erleichtert spätere Anpassungen.

## 3. Wo die Schlussfolgerungen zu weit gehen

### Ein Marktplatz bietet Zugang, garantiert aber keine Kunden

Der Optionsraum setzt stellenweise Store-Sichtbarkeit mit Kundengewinnung gleich. Auch dort brauchst du Suchbegriffe, Beispiele, Positionierung, Vertrauen und Pflege. Ohne Kaltvertrieb ist möglich; ohne Arbeit an der Kundengewinnung ist keine belastbare Planung.

Reserviere als Planungsannahme ungefähr ein Drittel der Wochenzeit für Auffindbarkeit und Auswertung. Baue zuerst ein Produkt und einen Kanal auf. Ein Portfolio vervielfacht sonst Wartung und Lernprobleme, bevor ein funktionierender Vertriebskanal existiert.

### Nutzung ist kein Umsatzbeleg

Die aktuelle Apify-Dokumentation berechnet Publisher-Gewinn als `0.8 × Umsatz − Plattformkosten`. Nutzung durch Gratispläne ist von dieser Gewinnberechnung ausgenommen. Öffentliche Nutzerzahlen zeigen deshalb weder zahlende Kunden noch Gewinn. [Apify PPE](https://docs.apify.com/actors/publishing/monetize/pay-per-event)

Die abgerufene Darstellung des Handelsregister-Actors zeigt 41 Gesamtnutzer und 20 monatlich aktive Nutzer; dein Snapshot nennt 47 beziehungsweise 20. Unterschiedliche Abrufstände sind möglich. Daraus lässt sich kein Trend ableiten. Der sichtbare Preis beträgt ab USD 8 je 1'000 Firmenrecords. Das ist zudem ein anderes Produkt als ein Ereignisfeed. [Actor-Listing](https://apify.com/memo23/handelsregister-scraper)

### Wenige erfolglose Angebote widerlegen keine ganze Kategorie

Die Sätze «Dateiverarbeitung hat kein Publikum» und «offizielle APIs haben keinen Wert» sind nicht ausreichend belegt. Unbekannt sind unter anderem Alter, Sichtbarkeit, Qualität und Gratisanteil der untersuchten Listings. Zulässig ist die engere Aussage: Die beobachteten Apify-Angebote lieferten damals kein starkes Nachfragesignal.

Kostenlose Daten können Teil eines bezahlten Produkts sein, wenn dieses Auswahl, Vergleich, Zuverlässigkeit oder einen fertigen Arbeitsablauf liefert. Die offene TED-Schnittstelle nennt kommerzielle Mehrwertdienste ausdrücklich als Anwendungsfall. [TED Search API](https://docs.ted.europa.eu/api/latest/search.html)

### Der Registerplan hat ungelöste Grundlagen

Die offizielle Portalstartseite meldet Überlastungen durch hohe Abrufzahlen. Eine aktuelle offizielle Freigabe für den vorgesehenen Archiv- und Weiterverkaufsbetrieb konnte ich nicht bestätigen. Die behaupteten 60 Abrufe pro Stunde sowie 300 Meldungen pro Tag und acht Wochen Verfügbarkeit bleiben hier unbestätigte Planungsannahmen. [Registerportal](https://www.handelsregister.de/)

Selbst ein bestätigtes technisches Limit wäre keine kommerzielle Nutzungslizenz. § 87b UrhG erfasst unter bestimmten Voraussetzungen auch wiederholte systematische Entnahmen kleiner Datenbankteile. Ob das auf dieses Vorhaben anwendbar ist, wurde nicht abschliessend geprüft. Die bisherige grüne Ampel ist deshalb zu eindeutig. [§ 87b UrhG](https://www.gesetze-im-internet.de/urhg/__87b.html)

Auch intern gibt es Widersprüche:

- Bei angenommenen 300 neuen Meldungen täglich und maximal 400 Abrufen täglich bleiben höchstens 100 für historische Meldungen, vor Listenabrufen und Wiederholungen. Acht Wochen entsprechen 16'800 Meldungen. Der vollständige Backfill dauert so nicht drei Wochen; währenddessen können ältere Meldungen verschwinden.
- «Keine Personennamen im Output» löst nicht automatisch die Verarbeitung solcher Daten in gespeicherten Rohtexten und Belegstellen.
- Die Spezifikation sieht nur einen primären Ereignistyp pro Meldung vor. Mehrere gleichzeitige Änderungen können damit für ein Monitoring verloren gehen.
- Ein Archiv wird erst dann ein wirtschaftlich wertvoller Bestand, wenn Nutzungsmöglichkeiten, Vollständigkeit, Qualität und zahlende Abnehmer zusammenkommen.

### Die Umsatzmechanik verlangt wesentlich mehr Volumen

Beim geplanten Preis von USD 8 je 1'000 Ereignissen ergeben 10'000 abrechenbare Ereignisse USD 80 Umsatz und USD 64 nach dem 20-Prozent-Anteil, vor Plattform- und eigenen Betriebskosten. Für USD 1'000 auf derselben Stufe wären 156'250 Ereignisauslieferungen monatlich nötig. Das sind Auslieferungen, nicht zwingend unterschiedliche Ereignisse.

Ein erster fremder bezahlter Lauf ist ein Lernsignal. Er belegt noch keinen Weg zu CHF 1'000–3'000 monatlich.

## 4. Drei konkrete Vorschläge

Alle Preise und Zeitangaben unten sind zu prüfende eigene Hypothesen. Aufwand meint einen begrenzten Demonstrator, kein produktionsreifes Gesamtprodukt.

| Priorität | Produkt | Käufer und Ergebnis | Preisexperiment | Demonstrator |
|---|---|---|---|---|
| 1 | Lieferantenpreislisten-Abgleich | Einkauf kleiner Handelsbetriebe: alte und neue Liste → Preisänderungen, fehlende Artikel, neue Artikel, unklare Zuordnungen | CHF 19 pro vollständigem Bericht; später CHF 29/Monat bei bestätigter Wiederholung | 12–20 h |
| 2 | Importprüfung für ein Zielformat | Betreiber eines konkreten ERP-/Shop-Workflows: Datei → verständliche Fehlerliste und geprüfte Exportdatei | CHF 19 pro Export oder CHF 29/Monat | 12–20 h nach Auswahl des Formats |
| 3 | Branchenbezogener TED-Monitor | Kleine Anbieter einer engen Leistung: relevante Ausschreibungen, Fristen und Änderungen mit Quellenlink | CHF 39–59/Monat | 16–24 h für ein Suchprofil |

### Vorschlag 1: Lieferantenpreislisten-Abgleich

**Versprechen:** «Sieh vor der Übernahme der neuen Lieferantenliste, welche Preise sich ändern und welche Artikel fehlen.»

Erster Umfang: zwei CSV-Dateien, eindeutiger Artikelschlüssel, genau eine Währung, absolute und prozentuale Preisänderungen, Dublettenhinweise und herunterladbarer Bericht. Mehrdeutige Zuordnungen bleiben offen. Keine automatische ERP-Änderung, keine PDF-Erkennung. Verarbeitung im Browser wäre eine prüfenswerte Variante, damit Dateien nicht hochgeladen werden müssen.

Wettbewerb ist vorhanden: Synkronizer verkauft Excel-Vergleich als Dauerlizenz; das abgerufene Standardbestellformular zeigt EUR 99. Power Query bietet bereits Tabellenzusammenführungen. Ein allgemeiner Tabellenvergleich wäre deshalb schwach positioniert. Die Hypothese ist, dass ein fertiger Einkaufsbericht ohne Formelkonfiguration einen Zusatznutzen hat. Das muss ein Nutzertest zeigen. [Synkronizer](https://www.synkronizer.com/purchase), [Microsoft Power Query](https://learn.microsoft.com/en-us/power-query/merge-queries-overview)

Kanaltest: eine Seite für «Lieferantenpreislisten vergleichen», ein frei bedienbares Beispiel und später gezielte Fachinhalte. Keine belegten Suchvolumina vorhanden. Dieser Weg hat weniger Quellenabhängigkeit als Registerdaten, dafür musst du die Auffindbarkeit selbst aufbauen. Ein Excel-Add-in erst bei belegtem Wunsch nach Nutzung direkt in Excel.

**Grösstes Risiko:** Die Aufgabe tritt nur jährlich auf oder bestehende Excel-Vorlagen reichen. Dann passt eher ein Einzelkauf als ein Abo; das wäre ein kleines Softwareprodukt, aber keine verlässliche MRR-Quelle.

### Vorschlag 2: Importprüfung für genau ein Zielformat

**Versprechen:** «Finde Fehler vor dem Import und erhalte eine Datei, die den dokumentierten Formatregeln entspricht.»

Beispiele für Regeln: Pflichtfelder, doppelte Artikelnummern, führende Nullen, Dezimaltrennzeichen, erlaubte Werte. Unklare Werte werden erklärt statt geraten. Versprich nur prüfbare Dateiregeln; ohne Zugriff aufs Zielsystem kannst du nicht jeden Importfehler ausschliessen.

CSVbox bietet bereits Mapping und Validierung mit bezahlten Tarifen. Das belegt ein kommerzielles Angebot in der Kategorie, keine freie Nische. Unsere Differenzierung müsste eine besonders gute Prüfung eines spezifischen Zielformats für Fachanwender sein. [CSVbox Preise und Funktionen](https://csvbox.io/pricing/)

Kanaltest: Suchanfragen nach konkreten Importfehlermeldungen, passende Integrationsverzeichnisse und ein kostenloser kleiner Dateicheck. Zuerst einen Workflow ausserhalb des in deinen Notizen noch ungeklärten Arbeitgeberbereichs auswählen.

**Grösstes Risiko:** Viele Sonderfälle machen aus dem Produkt individuelle Datenbereinigung. Keine kundenspezifischen Mappings im ersten Angebot; bei jedem zweiten Testfall mit Sonderentwicklung ist der Umfang falsch gewählt.

### Vorschlag 3: TED-Monitor für eine einzelne Branche

**Versprechen:** «Erhalte passende öffentliche Ausschreibungen für deine Leistung und erkenne relevante Friständerungen.»

TED stellt eine offizielle, ohne Authentifizierung nutzbare Such-API für veröffentlichte Vergabebekanntmachungen bereit. Das entschärft die technische Quellenfrage gegenüber dem Register-Scraper. Nutzungsbedingungen und Quellenhinweise sind vor Veröffentlichung trotzdem konkret zu prüfen. [TED API](https://docs.ted.europa.eu/api/latest/search.html)

Erster Umfang: eine Branche, eine Region, gespeichertes Suchprofil, Quellenlinks, nachvollziehbare Ein- und Ausschlussregeln. Keine Behauptung, sämtliche nationalen und lokalen Ausschreibungen abzudecken. Abgrenzung gegenüber TED selbst und bestehenden Diensten muss über bessere Relevanz erfolgen; Tenderlake bietet bereits Ausschreibungsmonitoring an. [Tenderlake](https://www.tenderlake.com/pricing/index)

Kanaltest: eine öffentlich sichtbare Beispielauswahl für einen engen Suchbegriff. Branche erst auswählen, wenn Anzahl passender Bekanntmachungen und relevante Konkurrenz geprüft sind.

**Grösstes Risiko:** Wenig geeignete Ausschreibungen für kleine Anbieter oder zu viele Fehlalarme. Technisch offene Daten lösen die Vertriebsfrage nicht.

## 5. Welche bisherigen Ideen ich zurückstelle

| Idee | Empfehlung | Grund |
|---|---|---|
| Register-Actor | Pausieren | Quellenrechte, Abdeckung, Nachfrage für Ereignisse und Erlösvolumen ungeklärt |
| bexio-Beleg-Autopilot | Zurückstellen | Laut bestehendem Desk-Check API-Lücke, dichter Wettbewerb und persönliches Onboarding |
| Generisches .NET-Starterkit | Allenfalls später | Vertrieb an Entwickler und laufende Framework-Pflege sind ein eigener Geschäftsbereich |
| Generischer MCP-Server | Als spätere Schnittstelle | Das Protokoll liefert allein keinen Kundennutzen und keinen Akquisekanal |
| Mehrere Actors gleichzeitig | Vermeiden | Zerteilt das knappe Zeitbudget, bevor ein Kanal funktioniert |

## 6. Wirtschaftliche Zielgrösse

Reine Umsatzarithmetik, keine Absatzprognose; vor Gebühren, Rückerstattungen, Betriebskosten, Steuern und eigener Arbeitszeit:

| Modell | Für mindestens CHF 1'000/Monat | Für mindestens CHF 3'000/Monat |
|---|---:|---:|
| CHF 19 Einzelkauf | 53 Käufe jeden Monat | 158 Käufe jeden Monat |
| CHF 29 Monatsabo | 35 aktive zahlende Kunden | 104 aktive zahlende Kunden |
| CHF 59 Monatsabo | 17 aktive zahlende Kunden | 51 aktive zahlende Kunden |

Ein höherer Preis reduziert den Mengenbedarf, verlangt aber belegbar höheren Nutzen. Wiederkehrende Rechnungen sind erst gerechtfertigt, wenn der Arbeitsablauf tatsächlich wiederkehrt. Bestehende Verkaufswert-Multiplikatoren sind in dieser frühen Phase keine sinnvolle Entscheidungsgrundlage.

## 7. Nächster Test: vier Wochen, höchstens 32 Stunden

**Woche 1 – Problem und Kanal, 8 h:** Nur Vorschlag 1 prüfen. Zehn konkrete Problembelege sammeln, einschliesslich Produktbewertungen und öffentlich diskutierter Arbeitsabläufe; Datum, Zielgruppe und Originalquelle festhalten. Drei Alternativen einschliesslich Excel/Power Query vergleichen. Eine Beispieldatei und einen verständlichen Änderungsbericht erstellen. Noch keine Konten-, Server- oder Billing-Architektur.

**Woche 2 – Demonstrator, 8 h:** Nur CSV, eindeutige Artikelnummern, eine Währung und ein Bericht. Preisseite entwerfen, Begrenzungen erklären. Kostenlose Beispieldaten anbieten. Ein Kauf- oder Pilotinteresse darf nicht als bereits fertige Leistung dargestellt werden.

**Woche 3 – Sichtbarkeit, 8 h:** Engen Suchbegriff und eine öffentlich zugängliche Demo testen. Fachbeiträge oder Community-Veröffentlichungen nur dort, wo passend und erlaubt; keine Kaltansprache erforderlich. Optional ein begrenzter Suchanzeigen-Test bis CHF 75, erst nach gesondertem Entscheid. Keine Ausgaben oder Veröffentlichungen wurden mit dieser Analyse ausgelöst.

**Woche 4 – Verhalten prüfen, 8 h:** Herkunft der Besucher, gestartete Vergleiche, vollständige Berichte, Zahlungsinteresse und tatsächliche Käufe getrennt messen. Freiwilliges Feedback im Produkt ermöglichen.

Entscheidungsregeln als pragmatische Schwellen, nicht als statistischer Marktnachweis:

- Weniger als 50 passende Besucher: vor allem Kanal ungeklärt. Kein Urteil «keine Nachfrage»; keinen grossen Funktionsausbau beginnen.
- Mindestens 50 passende Besucher, aber kaum gestartete Vergleiche: Nutzen, Vertrauen oder Ansprache prüfen.
- Mehrere abgeschlossene Vergleiche, aber keine Käufe: Preis, Alternativen und verbleibenden Nutzen prüfen.
- Drei unabhängige zahlende Kunden: Anlass zum Weiterlernen, noch kein Beleg für Skalierbarkeit.
- Wiederholte Nutzung über zwei Arbeitszyklen: erst jetzt Abo testen.
- Kein Zugang zur Zielgruppe innerhalb des Zeitlimits: den Kanal wechseln oder die Hypothese parken.

**Entscheid für den nächsten Arbeitsschritt:** Eine kleine Demonstration des Preislisten-Abgleichs und ein überprüfbarer Kanaltest. Der Engpass ist derzeit der Nachweis, dass erreichbare Nutzer für das Ergebnis bezahlen.
