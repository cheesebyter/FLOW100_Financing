# H1 Desk-Check: bexio „Beleg-Autopilot“ für Treuhandbüros

**Stand:** 11.09.2026 · **Status:** Desk-Check abgeschlossen, Interviews und API-Spike ausstehend

---

## Ergebnis auf einen Blick

**Ampel: GELB.** Das Problem ist real: Mehrere Anbieter lösen genau dieses Thema. Genau deshalb ist H1 als „Portal für Belege“ aber bereits besetzt. Dazu kommt, dass bexio Treuhändern ein kostenloses Cockpit anbietet. Weiterverfolgen lohnt sich nur als **enger Keil** mit 2 Wochen Validierung und harten Abbruchkriterien.

| Kriterium | Befund | Bewertung |
|---|---|---|
| Nachfrage / Pain | 60–70 % der Mandate liefern Belege per E-Mail; manuelle Verarbeitung 2–3 min pro Beleg; mehrere spezialisierte Anbieter | 🟢 belegt |
| API-Machbarkeit | OAuth2/OIDC, Scopes für Buchhaltung/Dateien/Bank, Dateien mit Verwendungsnachweis, Dateien an Buchungen anhängbar. **Aber:** kein Endpoint für importierte Banktransaktionen gefunden, keine OpenAPI-Spec | 🟡 Spike nötig |
| Wettbewerb | bexio Cockpit (gratis, 1'300+ Treuhänder), TreuFlow (ab CHF 149/Monat, Belegportal + bexio), CustomerCore, Luota, Kontli, Accounto | 🔴 dicht |
| Plattform-Risiko | bexio kann eine Beleg-Nachforderung jederzeit gratis ins Cockpit einbauen | 🔴 hoch |
| Marktgrösse | ~1'000–1'300 Treuhandfirmen im bexio-Umfeld → Umsatzdeckel (siehe Abschnitt 4) | 🟡 begrenzt |
| Skill-Fit | OAuth, Sync, Regel-Engine, SQL | 🟢 sehr hoch |

---

## 1. API-Machbarkeit

**Belegt (bexio-Doku, Sept. 2026):**

- **Auth:** OAuth2 mit OpenID Connect über `auth.bexio.com/realms/bexio`. Für Tests gibt es Personal Access Tokens (60 Tage gültig) unter developer.bexio.com/pat. Der alte IdP wurde am 31.03.2025 abgeschaltet.
- **Scopes:** unter anderem `accounting`, `file`, `bank_account_show`, `bank_payment_show`, `kb_bill_show`, `kb_expense_show`.
- **Ressourcen:**
  - Konten und Kontengruppen
  - Manuelle Buchungen inkl. Dateien pro Buchungszeile (lesen/anhängen)
  - Journal
  - Dateien (hochladen, suchen, herunterladen, Vorschau, **Verwendung einer Datei abfragen**)
  - Bankkonten und Zahlungen
  - Kreditorenrechnungen und Ausgaben
  - Geschäftsjahre und MWST-Perioden
- **Rate Limits:** Limit pro Minute mit den Headern `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`; bei Überschreitung HTTP 429.
- **Keine OpenAPI-Definition** („plans to put it online“). In der Doku sind API-Versionen 2.0, 3.0 und 4.0 gemischt.

**Kritische Lücke:** Einen Endpoint, der **importierte Banktransaktionen** (E-Banking-Abgleich) auflistet, habe ich nicht gefunden. Der Banking-Bereich deckt nur Bankkonten und in bexio erstellte Zahlungen ab. Die Regel „Bankbewegung ohne Beleg“ lässt sich also wahrscheinlich **nicht direkt** abfragen.

**Möglicher Ersatz:** Das Journal lesen, Buchungen auf Aufwandkonten (Kontenklasse 4–6) ab einem Mindestbetrag filtern und gegen die Anhänge von manuellen Buchungen, Kreditoren und Ausgaben prüfen. Ob das Journal dafür die Quelle einer Buchung (Bankabgleich, manuell, Kreditor) eindeutig liefert, **muss der Spike zeigen**.

**Der API-Spike (≈ 4 h) muss 5 Fragen beantworten:**

1. Enthält jeder Journal-Eintrag eine Referenz auf seine Quelle (manuelle Buchung, Kreditor, Bankabgleich)?
2. Lässt sich pro Buchung zuverlässig feststellen, ob ein Beleg angehängt ist?
3. Wie erscheinen per E-Banking abgeglichene Bankbewegungen in der API?
4. Funktioniert es, eine Datei hochzuladen und an eine bestehende Buchung anzuhängen?
5. Gilt ein OAuth-Token für **eine** Firma? Wie greift ein Treuhänder mit einem Login auf viele Mandanten zu (App-Registrierung, Zustimmung pro Mandant)?

---

## 2. Wettbewerb

| Anbieter | Was | Preis | Überschneidung mit H1 |
|---|---|---|---|
| **bexio Cockpit** | 360°-Übersicht über alle Mandanten (auch Nicht-bexio), Prozessvorlagen, Aufgaben, Kennzahlen | **kostenlos**, 1'300+ Treuhänder | Mittel. Eine Beleg-Nachforderung wird nicht erwähnt, wäre aber eine naheliegende Erweiterung |
| **TreuFlow** | KI-Treuhandsoftware: Mandantenportal (Link, App, E-Mail), Belegerkennung, Bankabgleich, Fristen-Workflows; bexio, Abacus, Topal, Banana, AbaNinja | CHF 149 (30 Mandate) / 449 (150) / 990 (500) pro Monat | **Hoch**, deckt die Beleg-Einsammlung als Teil einer Suite ab |
| **CustomerCore Treuhand-Portal** | Mandanten laden Belege per App hoch, KI-Vorkontierung, weniger Nachfragen zu fehlenden Belegen (online seit 12/2025) | nicht öffentlich | **Hoch** |
| **Luota Treuhand-Portal** | Dokumentenaustausch, automatische To-do-Listen, Freigaben; M-Files-DMS | nicht öffentlich, 60+ Treuhänder | Mittel |
| **Kontli** | Buchhaltung für Klein-Mandate mit Foto-Belegen, Multi-Firmen-Übersicht, bexio-Import | auf Anfrage | Mittel |
| **Accounto** | Wird als Treuhand-Tool für Belege genannt | – | Offen, im Interview erfragen |
| **Swiss Shift, Brainhance** | Automations-Agenturen bzw. „digitale Mitarbeiter“ für Schweizer Treuhandbüros (u. a. n8n) | Projekt/Abo | Indirekt; bestätigt aber die Nachfrage nach dem Productized-Service-Fallback |
| **GetMyInvoices** | Rechnungen automatisch aus Portalen und E-Mails holen, inkl. bexio | Abo | Relevant für KMU-seitige Varianten |

**Einschätzung:** Der Markt ist aktiv, und Treuhänder zahlen für dieses Thema. Die Anbieter verkaufen aber **Suiten und Portale**. Eine Nische bleibt höchstens für kleine Büros, die kein weiteres Portal einführen wollen.

---

## 3. Wo bleibt eine Lücke? (Hypothese für die Interviews)

**Keil-Hypothese „Kein neues Portal“:**

- **Zielkunde:** Treuhandbüros mit 1–10 Mitarbeitenden und 10–60 bexio-Mandanten, die bexio (und evtl. das Cockpit) nutzen, aber **kein** kostenpflichtiges Portal wie TreuFlow oder CustomerCore.
- **Mandant braucht weder Login noch App:** Er bekommt eine Erinnerung per E-Mail mit Einmal-Link, der Upload landet direkt an der richtigen Buchung in bexio.
- **Treuhänder bleibt in bexio:** Das Tool läuft im Hintergrund, dazu ein Wochenreport „offene Belege pro Mandant“.
- **Preis:** CHF 29–59/Monat pro Büro, klar unter TreuFlow Basic (CHF 149).

**Ehrliche Schwäche:** Die Differenzierung ist dünn und schwer zu verteidigen. Wer ein Portal hat, braucht das Tool nicht. Wer keins hat, wechselt womöglich direkt zu einer Suite.

---

## 4. Marktdeckel (Einschätzung)

Basis: ca. 1'300 Treuhänder im bexio-Cockpit.

| Preis/Monat | 2 % Marktanteil (26 Büros) | 5 % Marktanteil (65 Büros) |
|---|---|---|
| CHF 29 | MRR CHF 754 | MRR CHF 1'885 |
| CHF 49 | MRR CHF 1'274 | MRR CHF 3'185 |
| CHF 79 | MRR CHF 2'054 | MRR CHF 5'135 |

Als Nebeneinkommen reicht das. Ohne Ausbau auf Lexware/DATEV (DE) oder weitere Funktionen liegt die Obergrenze aber bei wenigen tausend Franken MRR.

---

## 5. Empfehlung: 2-Wochen-Validierung (≈ 16 h)

| # | Schritt | Aufwand | Ergebnis |
|---|---|---|---|
| 1 | Anfrage an das bexio-Partnerteam (Entwurf unten): OAuth-App für Treuhänder mit vielen Mandanten, Marketplace-Konditionen, Beleg-Themen auf der Cockpit-Roadmap | 30 min | Plattform-Risiko und Konditionen |
| 2 | API-Spike mit Sandbox und Personal Access Token (Code unten), 5 Fragen aus Abschnitt 1 beantworten | 4 h | Technisch machbar ja/nein |
| 3 | 25 kleine Treuhandbüros mit bexio identifizieren (bexio-Treuhänder-Verzeichnis, LinkedIn, TREUHAND\|SUISSE-Sektionen, Netzwerk) | 1.5 h | Kontaktliste |
| 4 | 8 Interviews à 20 min (Leitfaden unten), **nur individuelle Anfragen**, keine Serienmails (UWG) | 5 h | Evidenz |
| 5 | Auswertung mit Prompt B aus dem Businessplan, Entscheid | 1 h | GO / NO-GO |

**Abbruch von H1, wenn einer dieser Punkte zutrifft:**

- ≥ 4 von 8 Büros nutzen schon ein Tool, das fehlende Belege einfordert, oder finden bexio Cockpit ausreichend.
- < 3 verbindliche Zusagen zu mindestens CHF 29/Monat.
- Der Spike zeigt: Buchungen ohne Beleg lassen sich nicht zuverlässig ermitteln.
- bexio bestätigt eine vergleichbare Funktion auf der Roadmap.

**Fallbacks bei Abbruch (in dieser Reihenfolge):**

1. **Productized Service „Treuhand-Automation“:** Die Automations-Agenturen am Markt zeigen, dass es dafür Nachfrage gibt. Das bringt schnelles Geld und echte Pains, aus denen später ein Produkt entstehen kann.
2. **Desk-Check H2** (QR-Rechnung + Zahlungsabgleich für CH-Shops).
3. **Dieselbe Idee für Lexware Office (DE)**, nach einem eigenen Wettbewerbs-Check.

---

## 6. Interviewleitfaden H1 (20 min)

**Einstieg:** Wie viele Mandanten betreut ihr, wie viele davon auf bexio? Wie viele Mitarbeitende?

1. Wie kommt ihr heute an fehlende Belege? Erzählt vom letzten Monatsabschluss oder der letzten MWST-Abrechnung.
2. Wie viele Belege fehlen typischerweise pro Mandant und Quartal? Wie viel Zeit kostet das Nachfordern?
3. Welche Belege fehlen am häufigsten: Kartenzahlungen, E-Mail-Rechnungen, Barbelege?
4. Welche Tools nutzt ihr dafür: bexio Cockpit, TreuFlow, CustomerCore, ein anderes Portal, E-Mail, Telefon? Warum dieses und nicht ein anderes?
5. Was hat euch an Portalen bisher gestört, oder warum nutzt ihr keins?
6. Wie reagieren eure Mandanten auf ein neues Login oder eine neue App?
7. Was müsste ein Tool können, damit ihr es nicht mehr selbst machen müsst? Was wäre ein No-Go (Datenschutz, Serverstandort, Sprache FR)?
8. *Nur bei klarem Pain:* Wir suchen 5 Pilotbüros. CHF <29–59>/Monat, im ersten Jahr 50 % Rabatt, Start in ca. 8 Wochen. Wärt ihr dabei?

**Zu notieren:** Anzahl Mandanten, Minuten pro Monat, bestehende Tools, Zitat zum Pain, Commitment ja/nein.

---

## 7. Entwurf: Anfrage an das bexio-Partnerteam

> **Betreff:** Integration im Bereich Beleg-Workflow für Treuhänder – Fragen zu API-Zugang und Marketplace
>
> Grüezi
>
> Ich entwickle eine Integration für Treuhandbüros, die mit bexio arbeiten, im Bereich Beleg-Workflow zwischen Treuhänder und Mandant. Bevor ich mit der Umsetzung starte, habe ich einige Fragen:
>
> 1. Wie registriere ich eine OAuth-App, mit der ein Treuhänder mehrere Mandanten-Firmen verbinden kann? Braucht es pro Mandant eine eigene Zustimmung bzw. ein eigenes Token?
> 2. Gibt es API-Zugriff auf importierte Banktransaktionen aus dem E-Banking-Abgleich, oder ist das geplant?
> 3. Welche kommerziellen Konditionen (Gebühren, Revenue Share) gelten für Marketplace- bzw. Treuhand-Marketplace-Partner?
> 4. Plant bexio im Cockpit oder in der Buchhaltung eigene Funktionen, um fehlende Belege bei Mandanten anzufordern? Ich möchte nichts bauen, was ihr ohnehin selbst liefert.
>
> Besten Dank und freundliche Grüsse
> Andreas Haslbeck

*Trade-off zu Frage 4:* Sie verrät die Idee, spart aber im Ernstfall Wochen. Die Formulierung bleibt bewusst allgemein.

---

## 8. API-Spike (C#, read-only)

**Ziel:** Herausfinden, welche Pfad-Versionen antworten, und die JSON-Strukturen lokal speichern, um die 5 Fragen zu beantworten. Der Spike nutzt **nur GET** und verändert keine Daten.
**Setup:**

- Sandbox- oder Test-Firma in bexio anlegen und einen Personal Access Token erstellen (developer.bexio.com/pat).
- Mit einem aktuellen .NET-SDK (8 oder neuer) ausführen:

```powershell
dotnet new console -n BexioSpike
cd BexioSpike
# Program.cs durch den Code unten ersetzen
$env:BEXIO_PAT = "<token>"   # nie committen, out/ in .gitignore aufnehmen
dotnet run
```

> Hinweis: Die Pfade sind **Kandidaten**. Die bexio-Doku mischt API-Versionen und bietet keine OpenAPI-Spec. Der Spike probiert pro Ressource mehrere Varianten und meldet, welche antwortet. Der Code ist nicht gegen die Live-API getestet und in dieser Umgebung nicht kompiliert. Ziel ist, dass er mit .NET 8 ohne Anpassung läuft.

```csharp
// BexioSpike – read-only Probe der bexio-API (.NET 8+)
using System.Net;
using System.Net.Http.Headers;
using System.Text.Json;

var token = Environment.GetEnvironmentVariable("BEXIO_PAT")
    ?? throw new InvalidOperationException("Umgebungsvariable BEXIO_PAT fehlt.");

using var http = new HttpClient { BaseAddress = new Uri("https://api.bexio.com/") };
http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
http.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));

var outDir = Directory.CreateDirectory("out").FullName;
var jsonOut = new JsonSerializerOptions { WriteIndented = true };

// Kandidaten pro Ressource – der erste Pfad mit HTTP 200 gewinnt.
var probes = new (string Name, string[] Paths)[]
{
    ("company_profile", new[] { "3.0/company_profile", "2.0/company_profile" }),
    ("accounts",        new[] { "2.0/accounts", "2.0/account" }),
    ("journal",         new[] { "3.0/accounting/journal", "2.0/journal" }),
    ("manual_entries",  new[] { "3.0/accounting/manual_entries", "2.0/manual_entry" }),
    ("files",           new[] { "3.0/files", "2.0/file" }),
    ("bank_accounts",   new[] { "3.0/banking/accounts", "2.0/bank_account" }),
    ("bills",           new[] { "4.0/purchase/bills", "2.0/kb_bill" }),
    ("expenses",        new[] { "4.0/expenses", "2.0/expense" }),
};

var found = new Dictionary<string, JsonElement>();

foreach (var (name, paths) in probes)
{
    foreach (var path in paths)
    {
        var (status, body) = await GetWithRetryAsync(http, path);
        Console.WriteLine($"{name,-16} {path,-34} {(int)status} {status}");
        if (status != HttpStatusCode.OK || body is null) continue;

        found[name] = body.Value;
        await File.WriteAllTextAsync(Path.Combine(outDir, $"{name}.json"),
            JsonSerializer.Serialize(body.Value, jsonOut));
        break;
    }
}

// Detail-Probes: Dateien einer manuellen Buchung und Verwendung einer Datei.
if (found.TryGetValue("manual_entries", out var entries) && FirstItem(entries) is JsonElement entry
    && entry.TryGetProperty("id", out var entryId)
    && entry.TryGetProperty("entries", out var lines) && FirstItem(lines) is JsonElement line
    && line.TryGetProperty("id", out var lineId))
{
    var path = $"3.0/accounting/manual_entries/{entryId}/entries/{lineId}/files";
    var (status, body) = await GetWithRetryAsync(http, path);
    Console.WriteLine($"{"entry_files",-16} {path,-34} {(int)status} {status}");
    if (body is not null)
        await File.WriteAllTextAsync(Path.Combine(outDir, "entry_files.json"), JsonSerializer.Serialize(body.Value, jsonOut));
}

if (found.TryGetValue("files", out var files) && FirstItem(files) is JsonElement file
    && file.TryGetProperty("id", out var fileId))
{
    var path = $"3.0/files/{fileId}/usage";
    var (status, body) = await GetWithRetryAsync(http, path);
    Console.WriteLine($"{"file_usage",-16} {path,-34} {(int)status} {status}");
    if (body is not null)
        await File.WriteAllTextAsync(Path.Combine(outDir, "file_usage.json"), JsonSerializer.Serialize(body.Value, jsonOut));
}

Console.WriteLine($"\nFertig. JSON-Dateien in: {outDir}");

static JsonElement? FirstItem(JsonElement el) =>
    el.ValueKind == JsonValueKind.Array && el.GetArrayLength() > 0 ? el[0] : null;

static async Task<(HttpStatusCode Status, JsonElement? Body)> GetWithRetryAsync(HttpClient http, string path)
{
    for (var attempt = 1; attempt <= 3; attempt++)
    {
        using var res = await http.GetAsync(path);

        if (res.StatusCode == HttpStatusCode.TooManyRequests)
        {
            var wait = res.Headers.TryGetValues("RateLimit-Reset", out var v)
                       && int.TryParse(v.FirstOrDefault(), out var s) ? s : 60;
            Console.WriteLine($"  429 – warte {wait}s (Versuch {attempt}/3)");
            await Task.Delay(TimeSpan.FromSeconds(wait));
            continue;
        }

        if (!res.IsSuccessStatusCode) return (res.StatusCode, null);

        var text = await res.Content.ReadAsStringAsync();
        try
        {
            using var doc = JsonDocument.Parse(text);
            return (res.StatusCode, doc.RootElement.Clone());
        }
        catch (JsonException)
        {
            Console.WriteLine($"  Antwort ist kein JSON: {text[..Math.Min(text.Length, 200)]}");
            return (res.StatusCode, null);
        }
    }
    return (HttpStatusCode.TooManyRequests, null);
}
```

**Auswertung mit Claude (Prompt):**

```
Hier sind JSON-Antworten der bexio-API (journal.json, manual_entries.json, files.json, entry_files.json, file_usage.json, bills.json, expenses.json).
Beantworte mit Belegen aus den Feldern:
1. Welche Felder im Journal verweisen auf die Quelle einer Buchung (manuell, Kreditor, Ausgabe, Bankabgleich)?
2. Wie lässt sich pro Buchung feststellen, ob ein Beleg (Datei) angehängt ist? Welche Aufrufe braucht es dafür?
3. Gibt es Hinweise auf per E-Banking abgeglichene Bankbewegungen? In welchem Objekt?
4. Skizziere eine Abfrage-Logik "Aufwandbuchungen ≥ CHF 50 ohne Beleg der letzten 90 Tage" inkl. Anzahl API-Calls pro 1'000 Buchungen.
5. Liste alles, was fehlt oder unklar ist.
```

---

## Quellen

- bexio API-Dokumentation: https://docs.bexio.com/
- bexio API / Sandbox: https://www.bexio.com/en-CH/api
- bexio Marketplace Partner: https://www.bexio.com/en-CH/marketplace/become-a-marketplace-partner
- bexio Cockpit: https://www.bexio.com/de-CH/treuhand/bexio-cockpit
- bexio Treuhand: https://www.bexio.com/de-CH/treuhand
- bexio „Keine Buchung ohne Beleg“: https://www.bexio.com/de-CH/beleg
- laravel-bexio (Referenz-Client): https://github.com/codebar-ag/laravel-bexio
- TreuFlow: https://treuflow.ch/
- CustomerCore Treuhand-Portal: https://customercore.ch/blog/das-treuhand-portal-von-customercore-ist-fuer-treuhaender-online
- Luota Treuhand-Portal: https://luota.ch/digitalisierungsloesungen-fuer-treuhaender/treuhand-portal/
- Kontli für Treuhänder: https://kontli.ch/treuhaender.html
- Swiss Shift Treuhand-Automatisierung: https://swiss-shift.ch/treuhand/
- Brainhance: https://brainhance.ch/
- Belegsammlung automatisieren (Mai 2026): https://invoicedataextraction.com/blog/treuhand-mandant-belegsammlung-automatisieren
- GetMyInvoices × bexio: https://www.it-management.today/getmyinvoices-importiert-jetzt-auch-dokumente-aus-bexio/
