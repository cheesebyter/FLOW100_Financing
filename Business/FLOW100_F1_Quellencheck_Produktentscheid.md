# F1 – Quellen- und Rechtscheck DE, Produktentscheid für Actor 1

**Stand:** 23.09.2026 · **Weg:** A (öffentliche deutsche Registerquellen, innerhalb ihrer Regeln) · Keine Rechtsberatung

---

## 1. Befund: Weg A kippt meine eigene Empfehlung K1

| Quelle | Zugang | Bewertung für Weg A |
|---|---|---|
| **Bundesanzeiger / Unternehmensregister** (Jahresabschlüsse) | Web-Oberfläche mit Captcha-Schutz, **keine offene offizielle API** für den allgemeinen Abruf | 🔴 **Raus.** Automatisierter Abruf bedeutet Captcha-Umgehung. Das ist nicht „sauber gearbeitet“ |
| **handelsregister.de – Suche und Dokumente** | Seit August 2022 gratis, aber nur über die Oberfläche. Nutzungsregeln nennen **max. 60 Abrufe pro Stunde**; Massenabfragen werden aktiv verfolgt | 🟠 Nur in kleiner Menge und langsam nutzbar. Ein Massen-Scraper verletzt die Regeln |
| **handelsregister.de – Registerbekanntmachungen** | Öffentliche amtliche Bekanntmachungen, **rund 300 pro Tag**, auf dem Portal nur **8 Wochen** sichtbar, keine API, keine Struktur | 🟢 **Machbar.** 300 Abrufe pro Tag liegen deutlich unter der 60-pro-Stunde-Grenze |
| **OffeneRegister.de** | Fertiger Datensatz, über 5 Mio. Firmen, **CC-BY 4.0, kommerzielle Nutzung erlaubt** | 🟢 Als Grundstock brauchbar, aber Kern aus 2017–2019, danach nur über Bekanntmachungen fortgeschrieben |
| **Kommerzielle Anbieter** (OpenRegister, handelsregister.ai) | REST-APIs ab ca. EUR 69/Monat, teils mit Freikontingent | ⚪ Als Vergleich und möglicher Zulieferer relevant, nicht als Grundlage |

**Konsequenz:** K1 (Jahresabschluss-Kennzahlen aus dem Bundesanzeiger) ist unter Weg A nicht umsetzbar. Genau deshalb hat der bestehende Anbieter dort auch wenig Konkurrenz — die Hürde ist nicht technisch, sie ist rechtlich.

---

## 2. Entscheidung: Actor 1 wird ein Ereignis-Feed, kein Abfrage-Tool

**Produkt:** „Deutsche Handelsregister-Ereignisse als strukturierte Daten“

- **Rohstoff:** die täglichen Registerbekanntmachungen (Neueintragungen, Änderungen, Löschungen, Liquidationen, Sitzverlegungen, Kapitalmassnahmen).
- **Das eigentliche Produkt:** nicht der Abruf, sondern die **Verwandlung von Amtsdeutsch in saubere Ereignisdaten** plus ein Archiv, das über die 8 Wochen des Portals hinausgeht.
- **Warum das trägt:** Das Portal zeigt unstrukturierten Text, nur acht Wochen lang, ohne Schnittstelle. Wer Firmenveränderungen beobachten will, muss heute selbst basteln. Genau das ist Friktion, und Friktion ist laut Signal-Check das, wofür bezahlt wird.
- **Dein Edge:** Ereignismodellierung, Normalisierung, stabile Identitäten über Zeit. Das ist Datenmodellierung, nicht Web-Gefrickel.

### Abgrenzung zum Wettbewerb

| Anbieter | Was er hat | Was ihm fehlt |
|---|---|---|
| memo23 (Apify) | Registersuche und Bundesanzeiger, echte Nutzung | Keine Ereignis-Logik, keine Historie über 8 Wochen hinaus |
| coezbek (GitHub, MIT) | Täglicher Abzug der Bekanntmachungen, archiviert | Rohdaten, kein Produkt, keine Struktur, kein Support |
| OpenRegister, handelsregister.ai | Vollwertige APIs mit Abo | Preis ab EUR 69/Monat, Abo statt Einzelnutzung |

Deine Position dazwischen: **strukturierte Ereignisse, nutzungsbasiert bezahlt, ohne Abo.**

---

## 3. Spielregeln, die du einhalten musst

1. **Tempo:** höchstens 60 Abrufe pro Stunde, verteilt, mit Pausen. Bei rund 300 Bekanntmachungen pro Tag genügt ein Lauf, der über mehrere Stunden verteilt arbeitet.
2. **Keine Umgehung:** kein Captcha-Bruch, keine Proxy-Rotation, kein Verschleiern des Clients. Eigener User-Agent mit Kontaktadresse.
3. **robots.txt respektieren**, keine Bereiche abrufen, die ausgeschlossen sind.
4. **Quelle nennen** in Ausgabe und Store-Beschreibung, inklusive Hinweis, dass es keine amtliche Auskunft ist.
5. **Personendaten:** Bekanntmachungen enthalten Namen von Geschäftsführern. Das ist DSGVO-relevant, inklusive Informationspflicht gegenüber den Betroffenen. **Standardmässig nur Firmenebene ausgeben**, Personennamen entweder weglassen oder erst später als bewusst gestaltete Option mit eigener Rechtsgrundlage.
6. **Grenzen:** Wenn das Portal blockt oder die Regeln ändert, wird gestoppt, nicht umgangen.

**Offene Rechtsfragen, die du kennen solltest:** Amtliche Bekanntmachungen selbst geniessen nach § 5 UrhG keinen Urheberrechtsschutz, ein Datenbankrecht des Portalbetreibers an der Sammlung ist aber denkbar. Die Nutzungsbedingungen des Portals sind zusätzlich zu beachten. Für den Umfang, den du planst, ist das Risiko überschaubar, aber nicht null. Wenn du hier Sicherheit willst, ist eine einmalige anwaltliche Kurzeinschätzung Geld wert.

---

## 4. Scope Actor 1 (MVP)

**Eingabe**

- Modus A: `date_from`, `date_to` → alle Bekanntmachungen im Zeitraum
- Modus B: Liste von Firmen oder Registernummern → nur deren Ereignisse
- Filter: Registergericht, Bundesland, Ereignistyp

**Ausgabe (ein Datensatz pro Ereignis)**

| Feld | Inhalt |
|---|---|
| `event_id` | stabile, ableitbare ID |
| `published_at` | Datum der Bekanntmachung |
| `court`, `register_type`, `register_number` | Registergericht, HRA/HRB, Nummer |
| `company_name`, `company_name_normalized`, `legal_form` | Firma und normalisierte Form |
| `event_type` | `new_registration`, `change`, `deletion`, `liquidation`, `capital_change`, `address_change`, `merger`, `other` |
| `event_subtype` | feinere Einordnung, wo erkennbar |
| `address` | Sitz, sofern in der Bekanntmachung enthalten |
| `capital_amount`, `capital_currency` | bei Kapitalmassnahmen |
| `raw_text` | Originaltext, optional abschaltbar |
| `source_url`, `fetched_at`, `parser_version` | Nachweis und Reproduzierbarkeit |
| `confidence` | pro erkanntem Feld, nie geraten |

**Bewusst nicht im MVP:** Personennamen, Jahresabschlüsse, Dokumente, Bonität, Verknüpfung zu Konzernstrukturen.

**Qualitätsversprechen im Listing:** Trefferquote je Feld ausweisen, unklare Felder bleiben leer, Originaltext auf Wunsch mitliefern. Das ist der sichtbare Unterschied zu den Klonen.

---

## 5. Technischer Aufbau

```
Täglicher Sammler (ausserhalb von Apify, auf deinem Hetzner-Server)
  → holt die Bekanntmachungen des Tages, langsam und höflich
  → legt Rohtext + Metadaten in PostgreSQL ab (das ist dein Archiv und dein Burggraben)

Parser (SDK-frei, eigenes Modul)
  → Amtsdeutsch → Ereignisobjekt, regelbasiert, mit Testfällen
  → Normalisierung von Firmenname, Rechtsform, Adresse, Beträgen

Apify Actor (dünne Hülle)
  → liest Anfrage, bedient sie aus deinem Archiv, nicht live von der Quelle
  → rechnet pro geliefertem Ereignis ab
```

Der entscheidende Punkt: **Der Actor greift nicht bei jeder Anfrage auf das Portal zu.** Er liefert aus deinem eigenen Archiv. Das hält die Last an der Quelle konstant niedrig, macht die Antwortzeiten gut und schafft nebenbei ein Gut, das dir gehört: die Historie.

**Kosten:** unverändert rund CHF 6 pro Monat für den Server, der Rest läuft über Apify.

---

## 6. Preis

- **USD 8 pro 1'000 gelieferte Ereignisse**, plus kleiner Startbetrag pro Lauf.
- Vergleichswerte: Registerdaten USD 8 pro 1'000, Bundesanzeiger-Rohtext ab USD 1.50, Registerdaten mit KI-Zusätzen USD 12.75.
- Später möglich: Monatspauschale für tägliche Überwachung einer festen Firmenliste. Das ist der Schritt von Einmalnutzung zu wiederkehrendem Umsatz und damit zum Asset.

---

## 7. Angepasster 4-Wochen-Plan

| Woche | Aufgaben | Ergebnis |
|---|---|---|
| **1** | Arbeitsvertrag prüfen · Apify-Konto samt KYC und Auszahlung · Server aufsetzen · Sammler bauen, der einen Tag Bekanntmachungen höflich einliest und roh speichert · robots.txt und Nutzungsregeln dokumentieren | Erste 300 Bekanntmachungen im eigenen Archiv |
| **2** | Parser für die vier häufigsten Ereignistypen · Testfälle aus 100 echten Bekanntmachungen · Trefferquote messen | Parser mit belegter Qualität |
| **3** | Actor bauen: Input-Schema, Abfrage gegen das Archiv, Pay-per-Event · README mit Feldliste, Trefferquoten, Grenzen und Quellenhinweis | Actor läuft auf der Plattform |
| **4** | Veröffentlichen, Preis setzen, zwei Beispiel-Läufe hinterlegen · Sammler als täglichen Job mit Überwachung · Wochencheck einrichten | Actor live, Archiv wächst täglich |

**Abbruchkriterien bleiben:** nach 6 Wochen live mindestens ein bezahlter Lauf von einer fremden Person, nach 12 Wochen mindestens 5 Nutzer oder 2 monatlich aktive. Zusätzlich: sofortiger Stopp, wenn die Quelle blockt oder die Bedingungen sich ändern.

---

## 8. Wenn du null Graubereich willst

Dann bleibt als Basis **OffeneRegister.de** unter CC-BY 4.0: kommerziell nutzbar, mit Namensnennung, aber im Kern von 2017 bis 2019. Daraus lässt sich kein Ereignis-Feed bauen, höchstens ein Nachschlagewerk mit veralteten Daten. Ehrlich gesagt: Das trägt kein Produkt. Dann wäre F2 (eigene API zu einem selbst gewählten Thema) der bessere Weg.

---

## Quellen

- Registerbekanntmachungen (Portal): https://www.handelsregister.de/rp_web/bekanntmachungen/welcome.xhtml
- Diskussion zu Open Data bei Registerbekanntmachungen, inkl. Menge und 8-Wochen-Grenze: https://discourse.opencode.de/t/opendata-zu-registerbekanntmachungen/4517
- Scraper-Projekt mit Hinweis auf 60 Abrufe pro Stunde (MIT): https://github.com/coezbek/registerbekanntmachungen
- bundesAPI-Projekt mit Hinweis auf Nutzungsregeln und Strafnormen: https://github.com/bundesAPI/handelsregister
- OffeneRegister.de, Daten und Lizenz: https://offeneregister.de/daten/
- Unternehmensregister-API: Status und Alternativen 2026: https://www.boniforce.de/unternehmensregister-api-2026/
- OpenRegister, Datenquellen und Aktualisierung: https://docs.openregister.de/sources/handelsregister
- handelsregister.ai, Preise als Marktvergleich: https://handelsregister.ai/en
- § 5 UrhG, amtliche Werke: https://www.gesetze-im-internet.de/urhg/__5.html
- Apify Pay per Event: https://docs.apify.com/platform/actors/publishing/monetize/pay-per-event
- Apify Auszahlungen: https://docs.apify.com/platform/actors/publishing/monetize/monthly-payouts
