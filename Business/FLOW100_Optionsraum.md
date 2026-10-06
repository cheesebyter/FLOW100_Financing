# FLOW100 – Optionsraum ohne Kaltvertrieb

**Stand:** 22.09.2026 · **Ziel:** erst lernen, dann CHF 1–3k/Monat, langfristig ein verkaufbares Asset · **Regeln:** kein Kaltvertrieb; Dienstleistung nur, wenn Anfragen von selbst kommen

---

## 0. Was deine Antworten verändern

| Deine Vorgabe | Konsequenz |
|---|---|
| Kein Kaltvertrieb | **Der Kanal entscheidet, nicht die Idee.** Nur Ideen, die über einen Marktplatz, eine Store-Suche, Doku/SEO oder ein Verzeichnis gefunden werden |
| Keine Stundenarbeit als Kern, aber Service als schneller Cash ok | Dienstleistung nur über **Inbound-Verzeichnisse**, zeitlich gedeckelt, als Finanzierung – nicht als Geschäftsmodell |
| Zuerst lernen, dann Einkommen, am Ende ein Asset | **Portfolio statt eine grosse Wette:** mehrere kleine Produkte, die denselben Kanal und dieselben Bausteine nutzen |
| Tiefes CRM-/ERP-Prozesswissen, viele Branchen | Stärke liegt bei **unspektakulären Geschäftsprozessen** (Daten, Formate, Abgleich, Migration, Reporting), nicht bei Consumer-Apps |
| Kein direkter Kundenzugang | Nachfrage muss **messbar** sein, bevor du baust – über Store-Daten, Preise der Konkurrenz und Suchverhalten statt über Gespräche |

**Der wichtigste Satz:** Ohne Vertrieb ist die Wahl des Kanals die eigentliche Strategie. Suche zuerst einen Ort, an dem Kunden von selbst suchen und bezahlen, und dann ein Problem, das dort gelöst werden will.

**Eine Korrektur:** „Zu ehrlich“ ist kein Nachteil in Marktplätzen mit Bewertungen, in Dokumentation, in technischen Inhalten und bei Inbound-Anfragen. Ein Nachteil ist es nur bei Kaltakquise. Auch Problem-Interviews sind kein Verkauf – wenn du sie später doch machen willst, kostet dich das nichts ausser Zeit.

---

## 1. Die Landkarte

Zwei Achsen: **Wer bringt die Kunden?** und **Was verkaufst du?**

| | Zeit (Service) | Einmaliges Artefakt | Wiederkehrender Nutzen |
|---|---|---|---|
| **Plattform bringt Kunden** | Inbound-Verzeichnisse (n8n-Partner, Upwork, Fiverr, Malt) | Marktplatz-Vorlagen, Digitalprodukte | **Marktplatz-Apps & Actors** (Apify, AppSource, Shopify, Atlassian), MCP-/Agent-Tools |
| **Du bringst Kunden** | Beratung, Projekte *(ausgeschlossen)* | E-Books, Kurse, Kits über eigene Reichweite | Eigener SaaS mit SEO/Ads, Newsletter |
| **Niemand bringt Kunden** | – | – | Kaufen statt bauen: bestehendes Micro-SaaS übernehmen |

Nur die **obere Zeile** passt vollständig zu deinen Regeln. Die mittlere Zeile braucht Reichweite, die du erst aufbauen müsstest. Die untere Zeile ist eine Kapitalfrage und kommt später.

---

## 2. Zwölf Optionsfamilien im Vergleich

Skala 1–5 (5 = bester Fit für deinen Rahmen).

| # | Familie | Kanal ohne Vertrieb | Skill-Fit | Automatisierung | Asset-Tauglichkeit | Zeit bis 1. Franken | **Fit** |
|---|---|---|---|---|---|---|---|
| 1 | **Marktplatz-Automationen (Apify Actors)** | Store-Suche, Billing inklusive | 5 | 5 | 3 | 4 | **4.4** |
| 2 | **API als Produkt** (Konvertierung, Validierung, Dokumente) | Doku-SEO, API-Verzeichnisse | 5 | 5 | 4 | 3 | **4.3** |
| 3 | **Microsoft-Ökosystem** (Excel-Add-in, Power-BI-Visual, Teams-App) | AppSource-Suche, 3 % Gebühr | 5 | 4 | 4 | 3 | **4.2** |
| 4 | **MCP-/Agent-Werkzeuge** | MCP-Registries, Marktplätze | 4 | 5 | 3 | 3 | **3.9** |
| 5 | Marktplatz-Apps klassisch (Shopify, Atlassian, monday) | Store-Suche | 4 | 4 | 4 | 2 | 3.6 |
| 6 | Dev-Bibliothek mit kommerzieller Lizenz (NuGet) | GitHub, Doku-SEO | 5 | 4 | 3 | 2 | 3.5 |
| 7 | Inbound-Dienstleistung über Verzeichnisse | Verzeichnis-Matching | 5 | 1 | 1 | 5 | 3.4 |
| 8 | Micro-SaaS mit Tool-SEO | transaktionale Suchanfragen | 4 | 4 | 5 | 2 | 3.4 |
| 9 | Digitale Produkte, Vorlagen, Workflow-Pakete | Marktplätze, Doku-SEO | 3 | 5 | 2 | 3 | 3.3 |
| 10 | Open Source mit Open-Core-Modell | GitHub, Ruf | 5 | 3 | 3 | 1 | 3.0 |
| 11 | Chrome-Extension | Web Store | 3 | 4 | 3 | 2 | 2.8 |
| 12 | Kaufen statt bauen (Micro-Acquisition) | Broker-Plattformen | 4 | 3 | 5 | 5 | 2.5 *(Budget fehlt)* |

---

## 3. Die vier stärksten Familien im Detail

### F1 – Marktplatz-Automationen (Apify Actors)

- **Was:** Du veröffentlichst kleine, eigenständige Automationen („Actors“) im Apify Store. Nutzer starten sie selbst, Apify übernimmt Hosting, Abrechnung und Kundenkonto.
- **Geld:** Nutzungsbasiert („Pay per Event“), du bekommst **80 %**. Übliche Preise liegen bei **USD 1–10 pro 1'000 Resultate**. Das Mietmodell läuft aus: seit 01.04.2026 keine neuen Miet-Actors, Abschaltung per 01.10.2026.
- **Warum du:** Datenaufbereitung, Formate, Schnittstellen, robuste Fehlerbehandlung – genau dein Handwerk.
- **Beispiele für dich:** Dokumente in strukturierte Daten wandeln (PDF-Rechnungen, Kontoauszüge, Preislisten), Daten zwischen Systemen abgleichen und Differenzberichte erzeugen, Massenimporte für CRM/ERP vorbereiten und validieren.
- **Risiken:** Preisdruck durch viele Anbieter, Plattformabhängigkeit, und bei Web-Scraping rechtliche Fragen. **Nimm Aufgaben ohne fremde Webseiten** (Datei rein, saubere Daten raus), dann entfällt das Rechtsthema weitgehend.
- **Erster Schritt:** Ein Actor in 2 Wochen, live, mit Preis.

### F2 – API als Produkt

- **Was:** Eine kleine, klar umrissene API mit Self-Serve-Anmeldung. Kein UI, kein Chat, kein Verkauf – nur Doku, Preis und Schlüssel.
- **Geld:** Staffelpreise nach Aufrufen, Abrechnung über Stripe oder einen Merchant of Record.
- **Warum du:** Reine Backend-Logik in .NET, deterministisch testbar, minimaler Support.
- **Beispiele:** Konvertierung und Validierung von Geschäftsdokumenten (z. B. E-Rechnungsformate), Erzeugung von Zahlungsteilen und Belegen, Prüf- und Abgleichlogik für Stammdaten, Adress- und Firmendaten-Normalisierung.
- **Distribution:** Dokumentation als Inhalt. Transaktionale und kommerzielle Suchanfragen sind von KI-Antworten in der Google-Suche deutlich weniger betroffen (8 % bzw. 5 % Auslösung) als Ratgeberthemen (36 %). Genau dort liegen API- und Tool-Suchen.
- **Risiken:** Preisverfall durch Open-Source-Alternativen; Nische muss eng und lästig genug sein.

### F3 – Microsoft-Ökosystem (Excel, Power BI, Teams)

- **Was:** Ein Add-in oder ein Power-BI-Visual, das eine konkrete Aufgabe in einer Fachabteilung löst, verkauft über den Microsoft Marketplace.
- **Geld:** Microsoft behält **3 %** bei Transaktionen über den Marktplatz. Für Power-BI-Visuals gibt es inzwischen ein eigenes Monetarisierungsmodell über AppSource.
- **Warum du:** Dein natürliches Umfeld. Käufer sind Controller, Buchhaltung, Vertriebsinnendienst – Menschen, deren Prozesse du kennst.
- **Beispiele:** Excel-Add-in für einen wiederkehrenden Abgleich (Bank, Lager, Provisionen), Power-BI-Visual für eine Darstellung, die es nicht gibt, Teams-App für eine Freigabe, die heute per Mail läuft.
- **Risiken:** Einkauf läuft oft über die IT, dadurch längere Zyklen. Als Einstieg eignen sich günstige Selbstbedienungs-Preise unter der Freigabegrenze vieler Firmen.

### F4 – MCP- und Agent-Werkzeuge

- **Was:** Werkzeuge, die KI-Agenten benutzen (MCP-Server), veröffentlicht in den neuen Registries und Marktplätzen.
- **Geld:** Entsteht gerade. Ein Marktplatz nennt ein 85/15-Modell mit Stripe Connect, daneben existieren Mikrozahlungen pro Aufruf. Diese Angaben stammen aus Branchenblogs, nicht von den Betreibern – vor einer Wette selbst prüfen.
- **Warum du:** Maximaler Lerneffekt im Bereich, der 2026 entsteht, und direkt anschlussfähig an deine Integrationsarbeit.
- **Beispiele:** Ein MCP-Server, der eine ERP- oder Buchhaltungs-API sauber für Agenten aufbereitet; Werkzeuge, die Geschäftsdaten prüfen statt nur abrufen.
- **Risiken:** Umsatz ungewiss, Ökosystem unreif. Als **Lern-Wette** einplanen, nicht als Einkommensquelle.

---

## 4. Schneller Cash ohne Kaltvertrieb

Wenn Geld früh fliessen soll, ohne dass du verkaufen musst: **Inbound-Verzeichnisse**. Du erstellst ein Profil mit klarem Leistungsversprechen, die Plattform bringt Anfragen, du antwortest sachlich – genau deine Stärke.

- **n8n Service Partner Directory** mit Matchmaking-Formular für Suchende
- Upwork, Fiverr, Freelancer für Automations-Aufträge
- Microsoft-/Plattform-Partnerverzeichnisse

**Regeln, damit es nicht zum Job wird:** maximal 4 h/Woche, Festpreis statt Stundensatz, nur Aufgaben annehmen, aus denen ein wiederverwendbarer Baustein entsteht, und jede Lieferung als möglichen Produktkern bewerten.

---

## 5. Validierung ohne ein einziges Kundengespräch

| Signal | Woher | Schwelle für „weiter“ |
|---|---|---|
| Bezahlte Konkurrenz existiert | Store-Listings, Preisseiten | Mindestens 2 Anbieter verlangen Geld dafür |
| Nachfrage im Store | Anzahl Nutzer, Bewertungen, Ranking | Vergleichbare Angebote haben sichtbare Nutzung |
| Beschwerden über Bestehendes | 1–3-Sterne-Bewertungen, Foren, GitHub-Issues | Mindestens 5 unabhängige Klagen zum selben Punkt |
| Suchverhalten | Keyword-Daten, transaktionale Begriffe | Suchanfragen mit Kaufabsicht vorhanden |
| Zahlungsbereitschaft | Smoke-Test: Landingpage mit Preis und Kauf-Button | Mindestens 3 Klicks auf „Kaufen“ pro 100 Besuchern |
| Realer Umsatz | Produkt live im Store mit Preis | Erster bezahlter Lauf innerhalb von 30 Tagen |

Der Clou bei Marktplätzen: Die letzte Stufe ist billiger als jede Umfrage. Du veröffentlichst die kleinste brauchbare Version mit Preis und lässt den Markt antworten.

---

## 6. Fahrplan: drei Wetten in sechs Monaten

| Zeitraum | Wette | Ziel | Abbruch, wenn |
|---|---|---|---|
| Woche 1–2 | **Aufsetzen:** Signal-Check für F1 und F2, Arbeitsvertrag prüfen, Konten anlegen (Store, Stripe/MoR, GitHub, VPS) | Zwei Ideen mit bestandenem Signal-Check | Kein Thema besteht den Check → andere Familie prüfen |
| Woche 3–6 | **Wette 1 (F1):** ein Actor im Store, mit Preis | Erster bezahlter Lauf | Nach 6 Wochen kein bezahlter Lauf |
| Woche 7–14 | **Wette 2 (F2 oder F3):** eine API oder ein Add-in, Self-Serve | 3 zahlende Nutzer oder CHF 100 Umsatz | Nach 8 Wochen kein zahlender Nutzer |
| Woche 15–24 | **Wette 3:** Ausbau des besten Ergebnisses statt Neustart, sonst F4 als Lern-Wette | CHF 300–500 MRR oder klarer Aufwärtstrend | Kein Wachstum → auf Inbound-Service umschalten und neu entscheiden |
| laufend | **Inbound-Profil** für Dienstleistung, max. 4 h/Woche | Finanzierung der Fixkosten | – |

Jede Wette hinterlässt drei Dinge: wiederverwendbaren Code, einen funktionierenden Kanal und Zahlen, mit denen die nächste Entscheidung besser wird.

---

## 7. Was das Ziel „verkaufbares Asset“ bedeutet

Kleine, inhabergeführte Software wird typischerweise mit dem **2- bis 4-Fachen des Jahresgewinns** gehandelt; bei privaten SaaS-Firmen mit geringem Wachstum nennt Flippa 3–5× ARR. Für dich heisst das konkret:

- Wiederkehrender Umsatz zählt mehr als Einmalzahlungen.
- **Nichts darf an deiner Person hängen.** Dokumentation, automatisiertes Deployment und ein Betrieb ohne Spezialwissen sind Teil des Werts.
- Niedrige Abwanderung und saubere Zahlen ab Tag eins: eigene Buchhaltung, klare Verträge, getrennte Konten.
- Rechenbeispiel: CHF 1'000 MRR sind CHF 12'000 Jahresumsatz. Bei rund 80 % Marge und dem 2- bis 4-Fachen des Gewinns ergibt das grob **CHF 19'000–38'000** Verkaufswert. Das ist die Grössenordnung, auf die du zuerst zielst – nicht die Million.

---

## 8. Nächste Schritte

1. Entscheide zwischen zwei Startpunkten: **F1 (Actor, schnellster echter Umsatz)** oder **F2 (API, bester Asset-Aufbau)**.
2. Signal-Check für 3 konkrete Ideen der gewählten Familie nach der Tabelle in Abschnitt 5 (ca. 3 h).
3. Konten und Grundgerüst aufsetzen (Store-Konto, Zahlungsanbieter, Repo, Deployment).
4. Kleinste Version live stellen, mit Preis.
5. Parallel: Inbound-Profil erstellen, aber erst nach der ersten Veröffentlichung.

---

## Quellen

- Apify Actor-Monetarisierung: https://docs.apify.com/academy/actor-marketing-playbook/store-basics/how-actor-monetization-works
- Apify Pay-per-Event: https://docs.apify.com/platform/actors/publishing/monetize/pay-per-event
- Stand der MCP-Monetarisierung 2026: https://dev.to/kirothebot/the-state-of-mcp-monetization-in-2026-where-builders-actually-get-paid-34k9
- MCP-Marktplätze und Registries: https://designrevision.com/blog/best-mcp-marketplaces-and-registries
- Microsoft Marketplace Gebühren: https://learn.microsoft.com/en-us/partner-center/marketplace-offers/marketplace-commercial-transaction-capabilities-and-considerations
- Power-BI-Visuals Monetarisierung: https://powerbi.microsoft.com/en-us/blog/new-monetization-option-for-power-bi-custom-visuals-through-appsource/
- Lizenzmodelle für AppSource-Visuals: https://learn.microsoft.com/en-us/power-bi/developer/visuals/custom-visual-licenses
- AI Overviews und organische Klickrate 2026: https://almcorp.com/blog/google-ai-overviews-organic-ctr-2026/
- Chrome-Extension-Statistik 2026: https://konabayev.com/blog/extension-monetization-statistics-2026/
- ExtensionPay (Zahlungen für Extensions): https://extensionpay.com/
- n8n Service Partner Directory: https://experts.n8n.io/
- SaaS-Bewertungsmultiplikatoren 2026: https://flippa.com/blog/saas-multiples/
- API-Monetarisierungsplattformen 2026: https://zuplo.com/learning-center/api-monetization-platform-comparison
- Shopify Revenue Share: https://shopify.dev/docs/apps/launch/distribution/revenue-share
- Atlassian Revenue Share 2026: https://www.atlassian.com/blog/development/updates-to-marketplace-revenue-share-2026
