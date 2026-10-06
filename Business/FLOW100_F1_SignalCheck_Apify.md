# F1 – Signal-Check Apify Store und Startplan

**Stand:** 23.09.2026 · **Entscheid:** F1 (Apify Actor) als erste Wette · **Status:** Signal-Check abgeschlossen, Ideenrichtung korrigiert

---

## 1. Das Wichtigste zuerst

Der Signal-Check widerlegt meinen eigenen Vorschlag aus dem Optionsraum. Ich hatte „Datei rein, saubere Daten raus“ empfohlen, um Rechtsfragen beim Scraping zu vermeiden. **Für genau diese Art Actor gibt es im Store praktisch keine Nachfrage.**

### Gemessene Nutzung (Stand 23.09.2026)

| Actor | Thema | Nutzer | Monatlich aktiv | Läufe | Preis |
|---|---|---|---|---|---|
| formnexa/invoice-receipt-data-extractor | Rechnungs-OCR | 2 | 1 | 72 | $10 / 1'000 |
| draeg82/csv-cleaner | CSV bereinigen | 2 | 1 | – | $10 / 1'000 |
| ceddl/bank-statement-standards-bridge | camt.053 / MT940 | 2 | 1 | 32 | $100 / 1'000 |
| siccscha/e-invoice-parser | XRechnung, ZUGFeRD | 2 | 1 | 56 | $50 / 1'000 |
| webdata_labs/lead-list-deduplicator | CRM-Dubletten | 2 | 1 | 180 | $0.20 / 1'000 |
| studio-amba/zefix-scraper | Zefix (CH) | 2 | 1 | 85 | ab $1.20 / 1'000 |
| parsebird/zefix-ch-scraper | Zefix (CH) | 2 | 2 | 24 | ab $0.79 / 1'000 |
| studio-amba/simap-scraper | Ausschreibungen CH | 2 | 1 | 35 | ab $1.20 / 1'000 |
| **memo23/handelsregister-scraper** | **Handelsregister DE** | **47** | **20** | **13'000** | **$8 / 1'000** |
| **memo23/bundesanzeiger-scraper** | **Bundesanzeiger DE** | **27** | **8** | **296** | **ab $1.50 / 1'000** |
| apify/website-content-crawler *(Referenz)* | Web-Crawling | 160'000 | 11'000 | 43 Mio. | ab $0.20 / 1'000 |

*Messhinweis: „2 Nutzer / 1 monatlich“ erscheint so oft identisch, dass es wie eine Untergrenze der Anzeige wirkt. Lies es als „unter der Messschwelle“, nicht als exakte Zahl.*

### Was daraus folgt

1. **Dokumenten- und Dateiverarbeitung hat auf Apify kein Publikum.** Auch teure, gut gemachte Actors (bis $100 pro 1'000) bleiben bei ein paar Dutzend Läufen.
2. **Nachfrage liegt bei Web-Quellen, die schwer zugänglich sind, in grossen Märkten.** Handelsregister.de und Bundesanzeiger haben echte Nutzung, beide vom selben Publisher, beide aktiv gepflegt.
3. **Schweizer Quellen tragen nicht.** Zefix ist über eine offizielle Schnittstelle und LINDAS frei abfragbar, der Markt ist klein – entsprechend tot sind die Listings.
4. **Der Store ist mit Klonen geflutet.** Zu jeder naheliegenden Idee gibt es 5–10 Listings, fast alle ohne Nutzung. Erster sein ist unmöglich. Es zählen Qualität, Pflege und Auffindbarkeit.

### Die Regel, die sich daraus ableitet

> **Wert = Zugangsfriktion der Quelle × Marktgrösse × Strukturierungsaufwand.**
> Eine offene, gut dokumentierte API hat keine Friktion und damit keinen Wert. Dateien, die der Nutzer selbst hochladen muss, haben kein Publikum. Bezahlt wird das Wegnehmen von echtem Aufwand an einer sperrigen Quelle in einem grossen Markt.

---

## 2. Der Haken, über den du entscheiden musst

Die Nachfrage auf Apify liegt beim Auslesen öffentlicher Portale. Das bedeutet:

- **Nutzungsbedingungen der Quelle** (handelsregister.de, bundesanzeiger.de) erlauben automatisiertes Abrufen nicht ohne Weiteres.
- **Datenbankschutzrecht** (in DE § 87b UrhG) kann bei systematischer Entnahme relevant sein.
- **Technische Gegenwehr**: Sperren, Captchas, Änderungen an der Seite bedeuten laufende Wartung.
- Apifys eigene Bedingungen verlangen, dass du dich an geltendes Recht und die Regeln der Quelle hältst.

Das ist keine Rechtsberatung, aber eine ehrliche Lagebeschreibung. Du hast drei Wege:

| Weg | Was das heisst |
|---|---|
| **A – Akzeptieren und sauber arbeiten** | Nur öffentlich zugängliche Daten, moderate Abfrageraten, robots.txt respektieren, keine personenbezogenen Massenprofile, Quelle transparent nennen, keine Umgehung von Sperren |
| **B – Nur offizielle Schnittstellen** | Rechtlich sauber, aber laut Messung ohne Nachfrage: genau dort sind die toten Listings |
| **C – Apify verlassen** | Zurück zu F2 (eigene API) oder F3 (Microsoft), wo die Distribution langsamer ist, das Thema aber frei wählbar bleibt |

**Meine Einschätzung:** Weg A ist vertretbar, wenn du bei öffentlich einsehbaren Firmendaten bleibst, keine Sperren umgehst und die Last gering hältst. Wenn dir dabei unwohl ist, ist Weg C ehrlicher als ein halbherziges A – und dann sollten wir F1 abbrechen, bevor du Zeit investierst.

---

## 3. Drei Kandidaten auf Basis der Messung

### K1 – Jahresabschluss-Kennzahlen aus dem Bundesanzeiger, strukturiert und mehrjährig *(Empfehlung)*

- **Nachfrage:** belegt. Der bestehende Bundesanzeiger-Actor hat 27 Nutzer, 8 monatlich aktive, 5,0 Sterne.
- **Lücke:** Der Platzhirsch parst Kennzahlen „best effort“ und liefert vor allem Text. Was fehlt, ist eine **saubere, mehrjährige Struktur**: Bilanz- und GuV-Positionen nach HGB-Gliederung, Vorjahresvergleich, abgeleitete Kennzahlen (Eigenkapitalquote, Anlagendeckung, Personalaufwandsquote), Einheitenbehandlung (Tsd./Mio.), und pro Wert ein Nachweis mit Originalbezeichnung und Fundstelle.
- **Dein Edge:** Du liest Bilanzen und kennst die Fallstricke. Das ist Domänenwissen, das ein KI-generierter Klon nicht hat.
- **Käufer:** Vertrieb und Credit-Risk-Teams, Datenanbieter, KI-Pipelines, die Firmenprofile anreichern.
- **Preis-Hypothese:** $10–15 pro 1'000 Datensätze. Der Nachbar nimmt $1.50 für Rohtext, ein anderer $12.75 für Registerdaten mit KI-Zusätzen.

### K2 – Veränderungs-Monitor statt Einmalabfrage

- **Idee:** Nicht abfragen, sondern überwachen. Eine Liste von Firmen wird täglich gegen neue Veröffentlichungen geprüft (Insolvenzen, Geschäftsführerwechsel, Sitzverlegung, neue Abschlüsse) und liefert nur die Deltas.
- **Warum interessant:** wiederkehrende Läufe statt Einmalnutzung, also stetiger Umsatz statt Strohfeuer. Passt exakt zum Ziel „wiederkehrend und übertragbar“.
- **Status:** Nachfrage nicht direkt gemessen, aber dieselbe Quelle wie K1. **Als zweiter Actor auf derselben Codebasis**, sobald K1 erste Läufe hat.

### K3 – Ausgabe im Zielsystem-Format *(kein eigener Actor, sondern Differenzierung)*

- Ausgabe zusätzlich als fertige Importdatei für gängige Systeme, inklusive Feldzuordnung und Prüfprotokoll. Das ist dein Prozesswissen, kostet wenig Zusatzaufwand und ist im Listing ein sichtbarer Unterschied.

**Verworfen:** Dokumenten-Konverter, CSV-Bereinigung, Zefix, simap, E-Rechnungs-Parser – alle mit gemessener Nachfrage nahe null.

---

## 4. Startplan, 4 Wochen

| Woche | Aufgaben | Ergebnis |
|---|---|---|
| **1** | Arbeitsvertrag prüfen · Apify-Konto, KYC und Auszahlung einrichten · Quelle technisch prüfen: Abrufwege, Struktur der Veröffentlichungen, Sperrverhalten · Nutzungsbedingungen lesen und Entscheid A/B/C festhalten | Go oder Stopp, dokumentiert |
| **2** | Kern bauen: Abruf, Parser für zwei Abschlussarten, Normalisierung, Nachweisfelder · lokal gegen 30 echte Abschlüsse testen | Parser mit gemessener Trefferquote |
| **3** | Actor verpacken: `actor.json`, Input-Schema, Dockerfile, Pay-per-Event-Konfiguration · Fehlerfälle, Wiederholungen, Ratenbegrenzung · README als Verkaufsseite schreiben | Actor läuft auf der Plattform |
| **4** | Preis setzen, veröffentlichen, in den Store-Kategorien einordnen · zwei Beispiel-Läufe als „Examples“ hinterlegen · Wartungsroutine aufsetzen (wöchentlicher Testlauf, Alert bei Strukturänderung) | Actor live mit Preis |

**Qualitätsmassstab statt Featureliste:** Trefferquote pro Feld messen und im README ausweisen. Kein Wert wird geraten; nicht sicher erkannte Felder bleiben leer. Genau das ist der Unterschied zu den Klonen.

### Abbruch- und Erfolgskriterien

- **Nach 6 Wochen live:** mindestens 1 bezahlter Lauf von einer fremden Person. Sonst Positionierung oder Titel ändern, nicht den Code.
- **Nach 12 Wochen:** mindestens 5 Nutzer oder 2 monatlich aktive. Sonst K1 einfrieren und K2 oder F2 starten.
- **Jederzeit:** Wenn die Quelle blockt oder die Bedingungen es verbieten, sofort stoppen.

### Auszahlung und Formales

- Abrechnung erfolgt monatlich: Rechnung wird am 11. erzeugt, Freigabe bis 14., danach Auszahlung.
- **Mindestbetrag:** USD 20 bei PayPal und Wise, USD 100 bei anderen Wegen. Niedrigere Beträge werden vorgetragen.
- Identitätsprüfung (KYC) ist Voraussetzung. Für die Schweiz sind PayPal oder Wise wegen Gebühren und Laufzeit sinnvoller als eine Auslandsüberweisung.
- Steuerlich bleibt es Nebenerwerb: ab dem ersten Franken deklarieren, AHV-Freigrenze CHF 2'500 Gewinn pro Jahr.

---

## 5. Technisches Grundgerüst

**Sprachwahl:** Actors sind Docker-Container, du kannst **jede Sprache** verwenden. SDKs gibt es aber nur für JavaScript und Python, und das SDK übernimmt Input, Dataset und die Abrechnung der Events. Für den ersten Actor ist **Python** der schnellere Weg; C# lohnt sich erst, wenn du den Parser später in eine eigene API (F2) hebst. Halte die Parser-Logik deshalb von Anfang an in einem eigenen Modul, unabhängig vom Apify-SDK.

### `.actor/actor.json`

```json
{
  "actorSpecification": 1,
  "name": "de-financials-extractor",
  "title": "German Annual Financials — structured multi-year",
  "version": "0.1",
  "buildTag": "latest",
  "dockerfile": "../Dockerfile",
  "input": "./input_schema.json",
  "storages": { "dataset": "./dataset_schema.json" }
}
```

### `.actor/input_schema.json`

```json
{
  "title": "Input",
  "type": "object",
  "schemaVersion": 1,
  "properties": {
    "companies": {
      "title": "Companies",
      "type": "array",
      "description": "Company names or register numbers, one entry per company",
      "editor": "stringList",
      "prefill": ["Musterfirma GmbH"]
    },
    "years": {
      "title": "Fiscal years",
      "type": "integer",
      "description": "How many fiscal years to return per company",
      "default": 3,
      "minimum": 1,
      "maximum": 10
    },
    "includeRawText": {
      "title": "Include raw filing text",
      "type": "boolean",
      "default": false
    }
  },
  "required": ["companies"]
}
```

### `Dockerfile`

```dockerfile
FROM apify/actor-python:3.12
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . ./
CMD ["python", "-m", "src.main"]
```

### `src/main.py` (Gerüst)

```python
import asyncio
from apify import Actor
from src.parser import parse_filing          # deine Logik, SDK-frei
from src.source import fetch_filings          # Abruf der Quelle

async def main() -> None:
    async with Actor:
        cfg = await Actor.get_input() or {}
        companies = cfg.get("companies", [])
        years = int(cfg.get("years", 3))
        include_raw = bool(cfg.get("includeRawText", False))

        # Ein Ereignis pro Firma, unabhängig von der Trefferzahl
        await Actor.charge(event_name="company_started", count=len(companies))

        for name in companies:
            try:
                filings = await fetch_filings(name, years=years)
            except Exception as exc:
                Actor.log.warning("Abruf fehlgeschlagen für %s: %s", name, exc)
                await Actor.push_data({"company": name, "status": "fetch_failed", "error": str(exc)})
                continue

            for filing in filings:
                record = parse_filing(filing)           # nie raten: unklare Felder bleiben None
                record["company"] = name
                record["status"] = "ok"
                if not include_raw:
                    record.pop("raw_text", None)
                await Actor.push_data(record)
                # Nur erfolgreich strukturierte Abschlüsse kosten
                await Actor.charge(event_name="statement_parsed")

if __name__ == "__main__":
    asyncio.run(main())
```

> Die Ereignisnamen (`company_started`, `statement_parsed`) musst du in der Actor-Konfiguration im Apify-Konto mit Preisen hinterlegen. Prüfe SDK-Signaturen und Feldnamen gegen die aktuelle Doku – dieses Gerüst ist ungetestet.

### README-Struktur (das ist deine Verkaufsseite und deine Auffindbarkeit)

1. Ein Satz: Was kommt rein, was kommt raus, für wen.
2. Beispiel-Output als Tabelle mit echten Feldern.
3. Feldliste mit Bedeutung, Einheit und Trefferquote.
4. Preisbeispiel: „1'000 Abschlüsse kosten rund $X“.
5. Grenzen offen benennen: Was der Actor nicht kann und wann Felder leer bleiben.
6. Rechtlicher Hinweis zur Quelle und zum Verwendungszweck.

Punkt 5 ist unüblich und wirkt genau deshalb. Ehrliche Grenzen sind bei technischen Käufern ein Kaufargument.

---

## 6. Offene Punkte

- Entscheid A, B oder C aus Abschnitt 2 – das ist deine Entscheidung, nicht meine.
- Prüfen, wie der bestehende Bundesanzeiger-Actor konkret ausgibt, um die Lücke zu bestätigen (ein Testlauf kostet wenige Cent).
- Klären, wie viele Abschlüsse pro Monat überhaupt neu veröffentlicht werden, um den Markt grob zu dimensionieren.

---

## Quellen

- Apify Actor-Monetarisierung: https://docs.apify.com/academy/actor-marketing-playbook/store-basics/how-actor-monetization-works
- Apify Pay per Event: https://docs.apify.com/platform/actors/publishing/monetize/pay-per-event
- Apify Auszahlungen: https://docs.apify.com/platform/actors/publishing/monetize/monthly-payouts
- Apify Store Publishing Terms: https://docs.apify.com/legal/store-publishing-terms-and-conditions
- Eigene Sprache per Dockerfile: https://docs.apify.com/academy/deploying-your-code/docker-file
- Handelsregister-Scraper (Referenzwert Nachfrage): https://apify.com/memo23/handelsregister-scraper/api
- Bundesanzeiger-Scraper (Referenzwert Nachfrage): https://apify.com/memo23/bundesanzeiger-scraper
- Website Content Crawler (Referenz oben): https://apify.com/apify/website-content-crawler
- Zefix-Actor (Referenz tote Nische): https://apify.com/studio-amba/zefix-scraper
- E-Invoice-Parser (Referenz tote Nische): https://apify.com/siccscha/e-invoice-parser/api
- camt.053/MT940-Konverter (Referenz tote Nische): https://apify.com/ceddl/bank-statement-standards-bridge/api/openapi
- Nebenerwerb Schweiz (AHV, Steuern): https://pfeffersack.ch/lexikon/nebenerwerb
