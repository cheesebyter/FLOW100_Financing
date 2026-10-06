# DataBridge – Arbeitsprobe für zuverlässige Datenimporte

Zwei unterschiedlich aufgebaute Kundenlisten werden in eine geprüfte Importdatei überführt. Identische Dubletten werden entfernt, widersprüchliche Kundendaten vollständig zurückgehalten. Alle Beispieldaten sind erfunden. DataBridge ist ein vorläufiger Name.

## Demo starten

Voraussetzung: Windows mit .NET 10 SDK (auf diesem Rechner vorhanden).

**`Start-Demo.cmd` doppelklicken.** Nach der Verarbeitung öffnet sich der Ergebnisbericht im Browser. Die Anwendung verarbeitet Dateien ausschliesslich lokal und benötigt keine zusätzlichen Bibliotheken oder externen Dienste.

Alternativ im Projektordner:

```powershell
dotnet run --project DataBridge -- samples output
dotnet run --project DataBridge -- --self-test
```

## Enthaltene Dateien

- `samples/kunden_crm.csv`: sechs Datensätze, deutsche Spaltennamen, Semikolon als Trennzeichen.
- `samples/kunden_erp.csv`: sechs Datensätze, englische Spaltennamen, Komma als Trennzeichen.
- `DataBridge/Program.cs`: Import, Validierung, Export, Bericht und ausführbare Prüfungen.
- `DEMO-SCRIPT.md`: Ablauf für eine kurze Bildschirmaufnahme.

Jeder Lauf erzeugt einen eigenen Unterordner unter `output`:

- `import_ready.csv`: ausschliesslich gültige und konfliktfreie Kunden.
- `review.csv`: Hinweise mit Quelldatei, Zeilennummer und vollständigen normalisierten Datensatzwerten; enthält auch entfernte identische Dubletten.
- `report.html`: lokal nutzbarer, visuell aufbereiteter Ergebnisbericht.

`output/report.html` ist eine aktualisierte Kopie des letzten Berichts. Die enthaltenen Dateilinks verweisen auf den jeweiligen Ergebnisordner auf diesem Rechner. Zum Weitergeben nach einem Ordnerwechsel die Demo am neuen Ort erneut ausführen; die HTML-Datei selbst zeigt die Ergebnisse auch ohne funktionierende CSV-Links.

## Erwartetes Ergebnis

| Kennzahl | Anzahl |
|---|---:|
| Eingelesene Zeilen | 12 |
| Importbereite Kunden | 6 |
| Zeilen zur manuellen Prüfung | 5 |
| Entfernte identische Dubletten | 1 |

Importiert werden K100, K101, K104, K106, K107 und K108. K100 kommt identisch doppelt vor. K102 hat zwei unterschiedliche E-Mail-Adressen: beide Versionen bleiben aus dem Import ausgeschlossen. K103 hat keine E-Mail-Adresse, K105 eine ungültige Adresse; einer weiteren Zeile fehlt die Kundennummer.

## Vereinbarte Regeln dieser Demo

1. Alle vier Zielfelder sind Pflichtfelder. Leerzeichen am Feldanfang und -ende werden entfernt.
2. Kundennummern werden exakt und unter Beachtung der Gross-/Kleinschreibung verglichen. Führende Nullen bleiben erhalten.
3. Gleiche Kundennummer und identische normalisierte Inhalte: die erste Version wird übernommen, jede weitere dokumentiert.
4. Gleiche Kundennummer und unterschiedliche Inhalte: sämtliche Versionen werden zur Prüfung zurückgehalten. Keine automatische Vermischung oder Auswahl einer vermeintlich richtigen Version.
5. E-Mail-Adressen werden auf Format geprüft, nicht auf Zustellbarkeit. Gross-/Kleinschreibung wird nicht automatisch verändert.
6. Fehlende oder doppelte Spaltennamen, fehlerhafte CSV-Strukturen und abweichende Spaltenanzahl führen zum Abbruch vor dem Ergebnisexport. Ein bestehender Bericht bleibt dann ein Bericht des vorherigen Laufs; sein Datum ist sichtbar.
7. Exportformat: UTF-8 mit BOM, Semikolon, in Anführungszeichen eingeschlossene Felder. Zusätzliche Quellspalten sind erlaubt und werden nicht exportiert.

Eine Zeile kann mehrere Prüfhinweise enthalten; die Kennzahl „Zeilen zur Prüfung“ zählt sie nur einmal.

## Umfang und Grenzen

Dies ist eine echte ausführbare Portfolio-Demo für CSV-Dateien. Native Excel-Dateien (`.xlsx`), frei konfigurierbare Zuordnungen, API-/SQL-Verbindungen, Zeitplanung und Installation auf Kundenrechnern sind mögliche separate Erweiterungen und in dieser Arbeitsprobe nicht enthalten. Excel-Tabellen können für diese Demo zunächst als passende CSV-Dateien gespeichert werden.

Die Kundendaten bleiben in den CSV-Dateien unverändert bis auf das beschriebene Trimmen. CSV-Dateien sind für einen Datenimport vorgesehen; bei fremden Eingabedaten können Tabellenprogramme führende Zeichen wie `=` als Formeln interpretieren. Zur Sichtprüfung ist der HTML-Bericht geeignet: alle Datenwerte werden HTML-kodiert.

Die Quelldateien werden nicht verändert. Die Demo ist auf kleine Beispieldaten ausgelegt und hält die Daten im Arbeitsspeicher. Vor einem Kundenauftrag werden Format, Beispieldaten, Prüfregeln, Zielsystem, Laufumgebung und Abnahme schriftlich vereinbart.

## Dein erstes Angebot

„Ich wandle Ihre Excel-/CSV-Exportdatei in eine geprüfte Importdatei für Ihr Zielsystem um. Sie erhalten ein wiederverwendbares Tool, einen nachvollziehbaren Prüfbericht und eine kurze Anleitung. Abstimmung und Übergabe erfolgen schriftlich.“

Testpreis: CHF 200 nur bei vorab geprüftem Gesamtaufwand von maximal drei Stunden. Enthalten: eine definierte Quellstruktur, ein Zielformat und vereinbarte Regeln. Zusätzliche Formate, Systemzugänge, Installation und neue Anforderungen separat kalkulieren. Die Demo ist keine Kundenreferenz und soll auch nicht als solche bezeichnet werden.
