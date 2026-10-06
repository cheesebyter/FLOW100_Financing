using System.Net;
using System.Net.Mail;
using System.Text;
using Microsoft.VisualBasic.FileIO;

if (args.Contains("--self-test")) { Checks.Run(); return 0; }
try
{
    var input = Path.GetFullPath(args.ElementAtOrDefault(0) ?? "samples");
    var output = Path.GetFullPath(args.ElementAtOrDefault(1) ?? "output");
    var rows = Engine.Read(Path.Combine(input, "kunden_crm.csv"), ";", ["Kundennummer", "Firma", "Email", "Ort"])
        .Concat(Engine.Read(Path.Combine(input, "kunden_erp.csv"), ",", ["customer_id", "company_name", "email_address", "city"])).ToList();
    var result = Engine.Process(rows);
    // Each execution has its own folder: earlier results are never silently overwritten.
    Directory.CreateDirectory(output);
    var run = Path.Combine(output, $"run-{DateTime.Now:yyyyMMdd-HHmmss}-{Guid.NewGuid().ToString("N")[..6]}");
    Directory.CreateDirectory(run);
    Reports.Write(result, run);
    File.Copy(Path.Combine(run, "report.html"), Path.Combine(output, "report.html"), true);
    Console.WriteLine($"Eingelesen: {rows.Count} | Importbereit: {result.Accepted.Count} | Zur Prüfung: {result.ReviewCount} | Identische Dubletten: {result.Duplicates}");
    Console.WriteLine($"Ergebnisse: {run}");
    return 0;
}
catch (Exception ex) when (ex is IOException or UnauthorizedAccessException or InvalidDataException or MalformedLineException or ArgumentException)
{
    Console.Error.WriteLine($"Abbruch: {ex.Message}");
    return 1;
}

record Customer(string Id, string Company, string Email, string City, string Source, long Line);
record Issue(Customer Row, string Code, string Message);
record Outcome(List<Customer> Accepted, List<Issue> Issues, int Total, int Duplicates)
{
    public int ReviewCount => Issues.Where(x => x.Code != "DUPLICATE").Select(x => (x.Row.Source, x.Row.Line)).Distinct().Count();
}

static class Engine
{
    public static List<Customer> Read(string path, string delimiter, string[] columns)
    {
        using var parser = new TextFieldParser(path, Encoding.UTF8) { HasFieldsEnclosedInQuotes = true, TrimWhiteSpace = false };
        parser.SetDelimiters(delimiter);
        var headers = parser.ReadFields()?.Select(x => x.Trim()).ToArray() ?? throw new InvalidDataException($"Leere Datei: {path}");
        if (headers.Distinct(StringComparer.OrdinalIgnoreCase).Count() != headers.Length)
            throw new InvalidDataException($"Doppelte Spaltennamen: {path}");
        var map = columns.Select(c => Array.FindIndex(headers, h => h.Equals(c, StringComparison.OrdinalIgnoreCase))).ToArray();
        if (map.Any(i => i < 0)) throw new InvalidDataException($"Erforderliche Spalten fehlen in {path}: {string.Join(", ", columns)}");
        var rows = new List<Customer>();
        while (!parser.EndOfData)
        {
            var line = parser.LineNumber;
            var fields = parser.ReadFields()!;
            if (fields.Length != headers.Length) throw new InvalidDataException($"Falsche Spaltenanzahl in {path}, Zeile {line}. Kein Export erstellt.");
            var values = map.Select(i => fields[i].Trim()).ToArray();
            rows.Add(new(values[0], values[1], values[2], values[3], Path.GetFileName(path), line));
        }
        return rows;
    }

    public static Outcome Process(List<Customer> rows)
    {
        var accepted = new List<Customer>();
        var issues = new List<Issue>();
        int duplicates = 0;
        foreach (var group in rows.GroupBy(r => r.Id, StringComparer.Ordinal))
        {
            var entries = group.ToList();
            var invalid = false;
            foreach (var row in entries)
            {
                var missing = new List<string>();
                if (row.Id.Length == 0) missing.Add("Kundennummer");
                if (row.Company.Length == 0) missing.Add("Firma");
                if (row.Email.Length == 0) missing.Add("E-Mail");
                if (row.City.Length == 0) missing.Add("Ort");
                if (missing.Count > 0) { issues.Add(new(row, "REQUIRED", $"Pflichtfelder fehlen: {string.Join(", ", missing)}")); invalid = true; }
                else if (!MailAddress.TryCreate(row.Email, out var mail) || mail.Address != row.Email || !mail.Host.Contains('.'))
                { issues.Add(new(row, "EMAIL", "E-Mail-Format ungültig (keine Zustellbarkeitsprüfung).")); invalid = true; }
            }
            // Missing IDs do not identify a common customer.
            if (group.Key.Length == 0) continue;
            var conflict = entries.Select(r => (r.Company, r.Email, r.City)).Distinct().Count() > 1;
            if (conflict)
            {
                foreach (var row in entries) issues.Add(new(row, "CONFLICT", "Gleiche Kundennummer, unterschiedliche Inhalte. Alle Versionen zurückgehalten."));
                continue;
            }
            if (invalid) continue;
            accepted.Add(entries[0]);
            foreach (var row in entries.Skip(1)) { issues.Add(new(row, "DUPLICATE", "Identisches Duplikat; erste Version übernommen.")); duplicates++; }
        }
        return new(accepted.OrderBy(r => r.Id, StringComparer.Ordinal).ToList(), issues, rows.Count, duplicates);
    }
}

static class Reports
{
    static string H(string value) => WebUtility.HtmlEncode(value);
    static string Csv(string value) => "\"" + value.Replace("\"", "\"\"") + "\"";
    static void WriteCsv(string path, IEnumerable<string[]> rows) => File.WriteAllLines(path, rows.Select(r => string.Join(';', r.Select(Csv))), new UTF8Encoding(true));
    public static void Write(Outcome result, string dir)
    {
        WriteCsv(Path.Combine(dir, "import_ready.csv"), new[] { new[] { "customer_id", "company_name", "email_address", "city" } }
            .Concat(result.Accepted.Select(r => new[] { r.Id, r.Company, r.Email, r.City })));
        WriteCsv(Path.Combine(dir, "review.csv"), new[] { new[] { "source", "line", "code", "message", "customer_id", "company_name", "email_address", "city" } }
            .Concat(result.Issues.Select(i => new[] { i.Row.Source, i.Row.Line.ToString(), i.Code, i.Message, i.Row.Id, i.Row.Company, i.Row.Email, i.Row.City })));
        var cards = string.Join("", new[] { (result.Total, "Eingelesene Zeilen"), (result.Accepted.Count, "Importbereite Kunden"), (result.ReviewCount, "Zeilen zur Prüfung"), (result.Duplicates, "Identische Dubletten") }.Select(x => $"<div class='card'><strong>{x.Item1}</strong><span>{x.Item2}</span></div>"));
        var customers = string.Join("", result.Accepted.Select(r => $"<tr><td>{H(r.Id)}</td><td>{H(r.Company)}</td><td>{H(r.Email)}</td><td>{H(r.City)}</td></tr>"));
        var issues = string.Join("", result.Issues.Select(i => $"<tr><td>{H(i.Row.Source)}<small>Zeile {i.Row.Line} · {H(i.Row.Id)}</small></td><td><span class='badge'>{H(i.Code)}</span></td><td>{H(i.Message)}</td></tr>"));
        var importLink = H(new Uri(Path.Combine(dir, "import_ready.csv")).AbsoluteUri);
        var reviewLink = H(new Uri(Path.Combine(dir, "review.csv")).AbsoluteUri);
        File.WriteAllText(Path.Combine(dir, "report.html"), $$"""
        <!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DataBridge · Importprüfung</title>
        <style>
        *{box-sizing:border-box}body{margin:0;background:#f1f5f9;color:#172b40;font:16px/1.6 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:48px 24px}header{background:#142c42;color:white;padding:36px;border-radius:18px}h1{font-size:36px;line-height:1.2;margin:10px 0}p{margin:12px 0}.eyebrow{font-size:12px;letter-spacing:2px;color:#7ce2cd;text-transform:uppercase}.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:24px 0}.card,section{background:white;border:1px solid #dce4eb;border-radius:12px;padding:24px}.card strong{display:block;font-size:38px;color:#087e72}.card span{font-size:14px}section{margin:20px 0;overflow:auto}h2{font-size:21px;margin:0 0 16px}table{border-collapse:collapse;width:100%;text-align:left;font-size:14px}th,td{padding:13px 10px;border-bottom:1px solid #e7edf2;vertical-align:top}th{color:#53677b}small{display:block;color:#60758a}.badge{font-size:11px;background:#edf2f7;border-radius:5px;padding:4px 8px}a.button{display:inline-block;background:#087e72;color:white;text-decoration:none;border-radius:8px;padding:10px 16px;margin:6px 8px 0 0}.note{color:#53677b;font-size:14px}footer{font-size:13px;color:#60758a}@media(max-width:700px){.cards{grid-template-columns:repeat(2,1fr)}header{padding:24px}h1{font-size:28px} }
        </style></head><body><main><header><div class="eyebrow">DataBridge / Arbeitsprobe</div><h1>Aus zwei Listen wird ein<br>geprüfter Datenimport.</h1><p>Zusammenführen. Validieren. Widersprüche sichtbar machen.</p></header>
        <div class="cards">{{cards}}</div><section><h2>Ihr Ergebnis</h2><p>Die Importdatei enthält nur vollständige, gültige und konfliktfreie Datensätze. Zurückgehaltene Zeilen und entfernte Dubletten sind nachvollziehbar dokumentiert.</p><a class="button" href="{{importLink}}">Importdatei öffnen</a><a class="button" href="{{reviewLink}}">Prüfbericht öffnen</a><p class="note">UTF-8 · Semikolon-getrennt · Alle Beispieldaten sind erfunden.</p></section>
        <section><h2>Importbereite Kunden</h2><table><thead><tr><th>Nummer</th><th>Firma</th><th>E-Mail</th><th>Ort</th></tr></thead><tbody>{{customers}}</tbody></table></section>
        <section><h2>Prüfung und Dubletten</h2><table><thead><tr><th>Herkunft</th><th>Status</th><th>Erklärung</th></tr></thead><tbody>{{issues}}</tbody></table></section>
        <footer>Erstellt am {{DateTime.Now:dd.MM.yyyy HH:mm:ss}} · Verarbeitung lokal auf Ihrem Rechner · Keine Datenübertragung an externe Dienste.<br>Die E-Mail-Prüfung kontrolliert das Format, nicht die Zustellbarkeit. Ein Prüfdatensatz kann mehrere Hinweise haben.</footer></main></body></html>
        """, new UTF8Encoding(false));
    }
}

static class Checks
{
    public static void Run()
    {
        var count = 0;
        void Assert(bool ok, string name) { if (!ok) throw new Exception($"FAILED: {name}"); Console.WriteLine($"PASS: {name}"); count++; }
        Customer Row(string id, string email, long line = 1) => new(id, "Firma", email, "Ort", "test.csv", line);
        var duplicate = Engine.Process([Row("1", "a@test.example"), Row("1", "a@test.example", 2)]);
        Assert(duplicate.Accepted.Count == 1 && duplicate.Duplicates == 1, "Identische Dublette wird einmal exportiert");
        var conflict = Engine.Process([Row("1", "a@test.example"), Row("1", "b@test.example", 2)]);
        Assert(conflict.Accepted.Count == 0 && conflict.ReviewCount == 2, "Konflikte halten alle Versionen zurück");
        var invalid = Engine.Process([Row("", "a@test.example"), Row("2", "invalid", 2)]);
        Assert(invalid.Accepted.Count == 0 && invalid.ReviewCount == 2, "Pflichtfelder und E-Mail werden geprüft");
        var mixed = Engine.Process([Row("1", "a@test.example"), Row("1", "invalid", 2)]);
        Assert(mixed.Accepted.Count == 0, "Ungültige Konfliktversion lässt keine gültige Version durch");
        var temp = Path.Combine(Path.GetTempPath(), "DataBridge-check-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(temp);
        var path = Path.Combine(temp, "input.csv");
        try
        {
            // Explicit fixture includes an embedded separator and escaped quotes.
            File.WriteAllText(path, "id;name;mail;city\n 7 ;\"See; \"\"Software\"\"\";a@test.example;Zürich\n");
            var parsed = Engine.Read(path, ";", ["id", "name", "mail", "city"]);
            Assert(parsed[0].Id == "7" && parsed[0].Company == "See; \"Software\"" && parsed[0].City == "Zürich", "CSV-Quoting, Umlaute und Trimmen");
            File.WriteAllText(path, "id;name;mail\n1;Firma;a@test.example\n");
            bool rejected = false;
            try { Engine.Read(path, ";", ["id", "name", "mail", "city"]); } catch (InvalidDataException) { rejected = true; }
            Assert(rejected, "Fehlende Spalte bricht Import ab");
            File.WriteAllText(path, "id;name;mail;city\n1;Firma;a@test.example\n");
            rejected = false;
            try { Engine.Read(path, ";", ["id", "name", "mail", "city"]); } catch (InvalidDataException) { rejected = true; }
            Assert(rejected, "Falsche Spaltenanzahl bricht Import ab");
        }
        finally { File.Delete(path); Directory.Delete(temp); }
        Console.WriteLine($"{count} Prüfungen erfolgreich.");
    }
}
