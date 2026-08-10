using System.Net;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace PiedonianCivicDocument;

internal static class AppConstants
{
    public const string AppName = "Piedonian Woods Civic Document";
    public const string FoundingName = "William Franklin Hoisington IV";
    public const string FoundingCapacity = "Founding Co-President — Founding Signature (sole and final)";
    public const string FoundingDateIso = "2026-08-10";
    public const string FoundingDateDisplay = "10 August 2026";
    public const string Seat = "805 N 4th, Merkel, TX 79536, United States of America";
    public const string DocumentTitle = "Constitution of the Piedonian Woods — Combined Civic Application Document";
    public const string Host = "127.0.0.1";
    public const int PreferredPort = 8777;
    public const string ClosureLegend = "FOUNDING SIGNATURE CLOSED — DO NOT RE-SIGN";
}

internal static class Paths
{
    public static string AppRoot =>
        AppContext.BaseDirectory.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);

    public static string WwwRoot => Path.Combine(AppRoot, "wwwroot");
    public static string ContentRoot => Path.Combine(AppRoot, "Content");
    public static string DataDir
    {
        get
        {
            var dir = Path.Combine(AppRoot, "data");
            Directory.CreateDirectory(dir);
            return dir;
        }
    }

    public static string RecordFile => Path.Combine(DataDir, "civic_signatures.json");
}

internal static class JsonUtil
{
    public static readonly JsonSerializerOptions Options = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        PropertyNameCaseInsensitive = true
    };
}

internal static class RecordStore
{
    private static readonly object Gate = new();

    public static JsonObject DefaultRecord()
    {
        return new JsonObject
        {
            ["version"] = 1,
            ["document"] = AppConstants.DocumentTitle,
            ["seat"] = AppConstants.Seat,
            ["founding"] = new JsonObject
            {
                ["status"] = "open",
                ["printedName"] = AppConstants.FoundingName,
                ["capacity"] = AppConstants.FoundingCapacity,
                ["requiredDate"] = AppConstants.FoundingDateIso,
                ["requiredDateDisplay"] = AppConstants.FoundingDateDisplay,
                ["signatureText"] = null,
                ["signatureImagePngB64"] = null,
                ["signedAtUtc"] = null,
                ["closureLegend"] = null,
                ["recordHash"] = null
            },
            ["citizens"] = new JsonArray(),
            ["optional"] = new JsonObject
            {
                ["coPresident"] = null,
                ["justice"] = null,
                ["witness"] = null,
                ["notary"] = null
            },
            ["updatedAtUtc"] = null
        };
    }

    public static JsonObject Load(string? overridePath = null)
    {
        lock (Gate)
        {
            var path = overridePath ?? Paths.RecordFile;
            if (!File.Exists(path))
            {
                var created = DefaultRecord();
                Save(created, path);
                return created;
            }

            var text = File.ReadAllText(path, Encoding.UTF8);
            var node = JsonNode.Parse(text) as JsonObject ?? DefaultRecord();
            MergeDefaults(node);
            return node;
        }
    }

    public static void Save(JsonObject record, string? overridePath = null)
    {
        lock (Gate)
        {
            record["updatedAtUtc"] = DateTime.UtcNow.ToString("O");
            var path = overridePath ?? Paths.RecordFile;
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            var tmp = path + ".tmp";
            File.WriteAllText(tmp, record.ToJsonString(JsonUtil.Options) + "\n", Encoding.UTF8);
            File.Move(tmp, path, overwrite: true);
        }
    }

    private static void MergeDefaults(JsonObject data)
    {
        var bas = DefaultRecord();
        foreach (var prop in bas)
        {
            if (!data.ContainsKey(prop.Key))
                data[prop.Key] = prop.Value?.DeepClone();
        }

        if (data["founding"] is JsonObject founding && bas["founding"] is JsonObject baseFounding)
        {
            foreach (var prop in baseFounding)
            {
                if (!founding.ContainsKey(prop.Key))
                    founding[prop.Key] = prop.Value?.DeepClone();
            }
        }

        data["optional"] ??= bas["optional"]?.DeepClone();
        data["citizens"] ??= new JsonArray();
    }

    public static int NextCitizenNumber(JsonObject record)
    {
        if (record["citizens"] is not JsonArray arr || arr.Count == 0)
            return 1;
        var max = 0;
        foreach (var item in arr)
        {
            if (item is JsonObject o && o["entryNo"] is JsonValue v && v.TryGetValue<int>(out var n))
                max = Math.Max(max, n);
        }
        return max + 1;
    }

    public static JsonObject PublicRecord(JsonObject record)
    {
        var clone = record.DeepClone()!.AsObject();
        clone["nextCitizenNo"] = NextCitizenNumber(record);
        // Also expose snake_case aliases used by legacy UI consumers
        NormalizeAliases(clone);
        return clone;
    }

    private static void NormalizeAliases(JsonObject clone)
    {
        if (clone["founding"] is JsonObject f)
        {
            Alias(f, "printedName", "printed_name");
            Alias(f, "requiredDate", "required_date");
            Alias(f, "requiredDateDisplay", "required_date_display");
            Alias(f, "signatureText", "signature_text");
            Alias(f, "signatureImagePngB64", "signature_image_png_b64");
            Alias(f, "signedAtUtc", "signed_at_utc");
            Alias(f, "closureLegend", "closure_legend");
            Alias(f, "recordHash", "record_hash");
        }

        if (clone["citizens"] is JsonArray citizens)
        {
            foreach (var c in citizens.OfType<JsonObject>())
            {
                Alias(c, "entryNo", "entry_no");
                Alias(c, "printedName", "printed_name");
                Alias(c, "grantedBy", "granted_by");
                Alias(c, "grantedDate", "granted_date");
                Alias(c, "signedDate", "signed_date");
                Alias(c, "signatureText", "signature_text");
                Alias(c, "signatureImagePngB64", "signature_image_png_b64");
                Alias(c, "recordedAtUtc", "recorded_at_utc");
            }
        }

        if (clone["optional"] is JsonObject opt)
        {
            if (opt["coPresident"] is JsonObject co)
            {
                Alias(co, "printedName", "printed_name");
                Alias(co, "signatureText", "signature_text");
                Alias(co, "recordedAtUtc", "recorded_at_utc");
                opt["co_president"] = co.DeepClone();
            }
            if (opt["justice"] is JsonObject ju)
            {
                Alias(ju, "printedName", "printed_name");
                Alias(ju, "signatureText", "signature_text");
                Alias(ju, "recordedAtUtc", "recorded_at_utc");
            }
            if (opt["witness"] is JsonObject w)
            {
                Alias(w, "printedName", "printed_name");
                Alias(w, "signatureText", "signature_text");
                Alias(w, "recordedAtUtc", "recorded_at_utc");
            }
            if (opt["notary"] is JsonObject n)
            {
                Alias(n, "printedName", "printed_name");
                Alias(n, "signatureText", "signature_text");
                Alias(n, "commissionExpires", "commission_expires");
                Alias(n, "recordedAtUtc", "recorded_at_utc");
            }
        }

        Alias(clone, "updatedAtUtc", "updated_at_utc");
        Alias(clone, "nextCitizenNo", "next_citizen_no");
    }

    private static void Alias(JsonObject obj, string camel, string snake)
    {
        if (obj.ContainsKey(camel) && !obj.ContainsKey(snake))
            obj[snake] = obj[camel]?.DeepClone();
    }

    public static string Sha256Hex(string text)
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(text));
        return Convert.ToHexString(bytes).ToLowerInvariant();
    }

    public static string FoundingHashPayload(JsonObject founding)
    {
        static string G(JsonObject o, string k) => o[k]?.GetValue<string?>() ?? "";
        return string.Join("|", new[]
        {
            G(founding, "printedName"),
            G(founding, "capacity"),
            G(founding, "requiredDate"),
            G(founding, "signatureText"),
            G(founding, "signatureImagePngB64"),
            G(founding, "signedAtUtc"),
            G(founding, "closureLegend")
        });
    }

    public static string? DataUrlToB64(string? dataUrl)
    {
        if (string.IsNullOrWhiteSpace(dataUrl))
            return null;
        var comma = dataUrl.IndexOf(',');
        if (comma < 0)
            return null;
        var header = dataUrl[..comma];
        if (!header.Contains("base64", StringComparison.OrdinalIgnoreCase))
            return null;
        var b64 = dataUrl[(comma + 1)..];
        try
        {
            _ = Convert.FromBase64String(b64);
        }
        catch
        {
            throw new InvalidOperationException("Invalid signature image encoding");
        }
        return b64;
    }

    public static string ExportMarkdown(JsonObject record)
    {
        var f = record["founding"]!.AsObject();
        var sb = new StringBuilder();
        sb.AppendLine("# Piedonian Woods — Executed Combined Civic Record");
        sb.AppendLine();
        sb.AppendLine($"**Document:** {record["document"]}");
        sb.AppendLine($"**Seat:** {record["seat"]}");
        sb.AppendLine($"**Exported (UTC):** {DateTime.UtcNow:O}");
        sb.AppendLine();
        sb.AppendLine("---");
        sb.AppendLine();
        sb.AppendLine("## Part A — Founding Signature");
        sb.AppendLine();
        sb.AppendLine($"- **Status:** {f["status"]}");
        sb.AppendLine($"- **Printed name:** {f["printedName"]}");
        sb.AppendLine($"- **Capacity:** {f["capacity"]}");
        sb.AppendLine($"- **Founding date:** {f["requiredDateDisplay"]}");
        sb.AppendLine($"- **Typed signature:** {f["signatureText"] ?? "—"}");
        sb.AppendLine($"- **Signed at (UTC):** {f["signedAtUtc"] ?? "—"}");
        sb.AppendLine($"- **Closure:** {f["closureLegend"] ?? "—"}");
        sb.AppendLine($"- **Record hash:** {f["recordHash"] ?? "—"}");
        sb.AppendLine();
        sb.AppendLine("## Part B — Citizen Signature Roll");
        sb.AppendLine();
        var citizens = record["citizens"] as JsonArray ?? new JsonArray();
        if (citizens.Count == 0)
        {
            sb.AppendLine("_No citizen entries yet._");
            sb.AppendLine();
        }
        else
        {
            foreach (var item in citizens.OfType<JsonObject>())
            {
                sb.AppendLine($"### Citizen Entry No. {item["entryNo"]}");
                sb.AppendLine();
                sb.AppendLine($"- **Printed name:** {item["printedName"]}");
                sb.AppendLine($"- **Citizenship granted by:** {item["grantedBy"]}");
                sb.AppendLine($"- **Date citizenship granted:** {item["grantedDate"]}");
                sb.AppendLine($"- **Signature of citizen:** {item["signatureText"]}");
                sb.AppendLine($"- **Date signed:** {item["signedDate"]}");
                sb.AppendLine($"- **Optional witness:** {item["witness"] ?? "—"}");
                sb.AppendLine($"- **Recorded at (UTC):** {item["recordedAtUtc"]}");
                sb.AppendLine();
            }
        }

        var opt = record["optional"] as JsonObject ?? new JsonObject();
        sb.AppendLine("## Optional acknowledgments");
        sb.AppendLine();
        void WriteOpt(string label, string key)
        {
            if (opt[key] is JsonObject o)
                sb.AppendLine($"- **{label}:** {o["signatureText"]} on {o["date"]}");
            else
                sb.AppendLine($"- **{label}:** not recorded");
        }
        WriteOpt("Co-President (Tommy James Lindsey)", "coPresident");
        WriteOpt("Justice of Democracy (Ramon Santiago IV)", "justice");
        WriteOpt("Witness", "witness");
        if (opt["notary"] is JsonObject n)
            sb.AppendLine($"- **Notary:** {n["signatureText"]} / {n["printedName"]} (commission {n["commissionExpires"] ?? "—"}) on {n["date"]}");
        else
            sb.AppendLine("- **Notary:** not recorded");
        sb.AppendLine();
        sb.AppendLine("**End of executed combined civic record**");
        sb.AppendLine();
        return sb.ToString();
    }
}

internal sealed class LocalServer
{
    private readonly HttpListener _listener = new();
    private readonly string _wwwRoot;
    private readonly string _contentRoot;
    private readonly string? _recordOverride;
    private int _port;

    public LocalServer(string wwwRoot, string contentRoot, string? recordOverride = null)
    {
        _wwwRoot = wwwRoot;
        _contentRoot = contentRoot;
        _recordOverride = recordOverride;
    }

    public string Url => $"http://{AppConstants.Host}:{_port}/";

    public void Start(int preferredPort = AppConstants.PreferredPort)
    {
        _port = FindFreePort(preferredPort);
        _listener.Prefixes.Add(Url);
        _listener.Start();
        _ = Task.Run(AcceptLoop);
    }

    public void Stop()
    {
        try { _listener.Stop(); } catch { /* ignore */ }
        try { _listener.Close(); } catch { /* ignore */ }
    }

    private static int FindFreePort(int start, int attempts = 30)
    {
        for (var port = start; port < start + attempts; port++)
        {
            var test = new HttpListener();
            try
            {
                test.Prefixes.Add($"http://{AppConstants.Host}:{port}/");
                test.Start();
                test.Stop();
                test.Close();
                return port;
            }
            catch
            {
                try { test.Close(); } catch { /* ignore */ }
            }
        }
        throw new InvalidOperationException("No free local port available for civic document app");
    }

    private async Task AcceptLoop()
    {
        while (_listener.IsListening)
        {
            HttpListenerContext ctx;
            try
            {
                ctx = await _listener.GetContextAsync().ConfigureAwait(false);
            }
            catch (HttpListenerException)
            {
                break;
            }
            catch (ObjectDisposedException)
            {
                break;
            }

            _ = Task.Run(() => Handle(ctx));
        }
    }

    private async Task Handle(HttpListenerContext ctx)
    {
        try
        {
            var req = ctx.Request;
            var res = ctx.Response;
            var path = req.Url?.AbsolutePath ?? "/";
            var method = req.HttpMethod.ToUpperInvariant();

            if (method == "GET")
            {
                await HandleGet(path, res).ConfigureAwait(false);
                return;
            }

            if (method == "POST")
            {
                await HandlePost(path, req, res).ConfigureAwait(false);
                return;
            }

            await WriteJson(res, 405, new { error = "method not allowed" }).ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            try
            {
                await WriteJson(ctx.Response, 500, new { error = ex.Message }).ConfigureAwait(false);
            }
            catch
            {
                // ignored
            }
        }
    }

    private async Task HandleGet(string path, HttpListenerResponse res)
    {
        if (path is "/" or "/index.html")
        {
            await WriteFile(res, Path.Combine(_wwwRoot, "index.html"), "text/html; charset=utf-8").ConfigureAwait(false);
            return;
        }

        if (path.StartsWith("/static/", StringComparison.Ordinal))
        {
            var rel = path["/static/".Length..].Replace('/', Path.DirectorySeparatorChar);
            var full = Path.GetFullPath(Path.Combine(_wwwRoot, rel));
            if (!full.StartsWith(Path.GetFullPath(_wwwRoot), StringComparison.Ordinal) || !File.Exists(full))
            {
                await WriteJson(res, 404, new { error = "not found" }).ConfigureAwait(false);
                return;
            }
            await WriteFile(res, full, MimeFromPath(full)).ConfigureAwait(false);
            return;
        }

        if (path == "/api/meta")
        {
            await WriteJson(res, 200, new
            {
                app = AppConstants.AppName,
                seat = AppConstants.Seat,
                foundingName = AppConstants.FoundingName,
                foundingCapacity = AppConstants.FoundingCapacity,
                foundingDateIso = AppConstants.FoundingDateIso,
                foundingDateDisplay = AppConstants.FoundingDateDisplay,
                document = AppConstants.DocumentTitle
            }).ConfigureAwait(false);
            return;
        }

        if (path == "/api/record")
        {
            var rec = RecordStore.PublicRecord(RecordStore.Load(_recordOverride));
            await WriteJsonNode(res, 200, rec).ConfigureAwait(false);
            return;
        }

        if (path == "/api/document" || path == "/api/document/combined")
        {
            var file = ResolveContent("PIEDONIAN_COMBINED_CIVIC_DOCUMENT.md");
            await WriteFile(res, file, "text/markdown; charset=utf-8").ConfigureAwait(false);
            return;
        }

        if (path == "/api/document/constitution")
        {
            await WriteFile(res, ResolveContent("CONSTITUTION_OF_THE_PIEDONIAN_WOODS.md"), "text/markdown; charset=utf-8").ConfigureAwait(false);
            return;
        }

        if (path == "/api/document/packet")
        {
            await WriteFile(res, ResolveContent("SIGNATURE_PACKET.md"), "text/markdown; charset=utf-8").ConfigureAwait(false);
            return;
        }

        if (path == "/api/export.json")
        {
            var body = RecordStore.Load(_recordOverride).ToJsonString(JsonUtil.Options);
            await WriteBytes(res, 200, Encoding.UTF8.GetBytes(body + "\n"), "application/json; charset=utf-8",
                "attachment; filename=\"civic_signatures.json\"").ConfigureAwait(false);
            return;
        }

        if (path == "/api/export.md")
        {
            var md = RecordStore.ExportMarkdown(RecordStore.Load(_recordOverride));
            await WriteBytes(res, 200, Encoding.UTF8.GetBytes(md), "text/markdown; charset=utf-8",
                "attachment; filename=\"executed_combined_civic_record.md\"").ConfigureAwait(false);
            return;
        }

        await WriteJson(res, 404, new { error = "not found" }).ConfigureAwait(false);
    }

    private string ResolveContent(string name)
    {
        var primary = Path.Combine(_contentRoot, name);
        if (File.Exists(primary))
            return primary;

        // Fall back to repo root Content copies when running from source tree
        var alt = Path.GetFullPath(Path.Combine(Paths.AppRoot, "..", "..", "..", "Content", name));
        if (File.Exists(alt))
            return alt;

        alt = Path.GetFullPath(Path.Combine(Paths.AppRoot, "..", "..", "..", "..", name));
        if (File.Exists(alt))
            return alt;

        throw new FileNotFoundException($"Content file not found: {name}");
    }

    private async Task HandlePost(string path, HttpListenerRequest req, HttpListenerResponse res)
    {
        using var reader = new StreamReader(req.InputStream, req.ContentEncoding);
        var raw = await reader.ReadToEndAsync().ConfigureAwait(false);
        JsonObject payload;
        try
        {
            payload = string.IsNullOrWhiteSpace(raw)
                ? new JsonObject()
                : JsonNode.Parse(raw) as JsonObject ?? new JsonObject();
        }
        catch
        {
            await WriteJson(res, 400, new { error = "Invalid JSON body" }).ConfigureAwait(false);
            return;
        }

        var record = RecordStore.Load(_recordOverride);

        if (path == "/api/founding")
        {
            var founding = record["founding"]!.AsObject();
            if (string.Equals(founding["status"]?.GetValue<string>(), "closed", StringComparison.OrdinalIgnoreCase))
            {
                await WriteJson(res, 409, new { error = "Founding signature is already closed and cannot be re-signed." }).ConfigureAwait(false);
                return;
            }

            var sigText = payload["signature_text"]?.GetValue<string?>()?.Trim()
                ?? payload["signatureText"]?.GetValue<string?>()?.Trim()
                ?? "";
            if (!string.Equals(sigText, AppConstants.FoundingName, StringComparison.Ordinal))
            {
                await WriteJson(res, 400, new { error = $"Typed signature must exactly match '{AppConstants.FoundingName}'." }).ConfigureAwait(false);
                return;
            }

            string? imgB64;
            try
            {
                imgB64 = RecordStore.DataUrlToB64(
                    payload["signature_image_data_url"]?.GetValue<string?>()
                    ?? payload["signatureImageDataUrl"]?.GetValue<string?>());
            }
            catch (Exception ex)
            {
                await WriteJson(res, 400, new { error = ex.Message }).ConfigureAwait(false);
                return;
            }

            var now = DateTime.UtcNow.ToString("O");
            founding["signatureText"] = sigText;
            founding["signatureImagePngB64"] = imgB64;
            founding["signedAtUtc"] = now;
            founding["closureLegend"] = AppConstants.ClosureLegend;
            founding["status"] = "closed";
            founding["printedName"] = AppConstants.FoundingName;
            founding["capacity"] = AppConstants.FoundingCapacity;
            founding["requiredDate"] = AppConstants.FoundingDateIso;
            founding["requiredDateDisplay"] = AppConstants.FoundingDateDisplay;
            founding["recordHash"] = RecordStore.Sha256Hex(RecordStore.FoundingHashPayload(founding));
            RecordStore.Save(record, _recordOverride);
            await WriteJsonNode(res, 200, RecordStore.PublicRecord(record)).ConfigureAwait(false);
            return;
        }

        if (path == "/api/citizen")
        {
            var printedName = GetStr(payload, "printed_name", "printedName");
            var grantedBy = GetStr(payload, "granted_by", "grantedBy");
            var grantedDate = GetStr(payload, "granted_date", "grantedDate");
            var signedDate = GetStr(payload, "signed_date", "signedDate");
            var witness = GetStr(payload, "witness");
            var sigText = GetStr(payload, "signature_text", "signatureText");
            if (printedName.Length == 0 || grantedBy.Length == 0 || grantedDate.Length == 0 || sigText.Length == 0)
            {
                await WriteJson(res, 400, new { error = "printed_name, granted_by, granted_date, and signature_text are required." }).ConfigureAwait(false);
                return;
            }

            string? imgB64;
            try
            {
                imgB64 = RecordStore.DataUrlToB64(
                    payload["signature_image_data_url"]?.GetValue<string?>()
                    ?? payload["signatureImageDataUrl"]?.GetValue<string?>());
            }
            catch (Exception ex)
            {
                await WriteJson(res, 400, new { error = ex.Message }).ConfigureAwait(false);
                return;
            }

            var entry = new JsonObject
            {
                ["entryNo"] = RecordStore.NextCitizenNumber(record),
                ["printedName"] = printedName,
                ["grantedBy"] = grantedBy,
                ["grantedDate"] = grantedDate,
                ["signedDate"] = signedDate.Length > 0 ? signedDate : DateTime.UtcNow.ToString("yyyy-MM-dd"),
                ["witness"] = witness.Length > 0 ? witness : null,
                ["signatureText"] = sigText,
                ["signatureImagePngB64"] = imgB64,
                ["recordedAtUtc"] = DateTime.UtcNow.ToString("O")
            };
            (record["citizens"] as JsonArray)!.Add(entry);
            RecordStore.Save(record, _recordOverride);
            await WriteJsonNode(res, 200, RecordStore.PublicRecord(record)).ConfigureAwait(false);
            return;
        }

        if (path == "/api/optional/co_president" || path == "/api/optional/coPresident")
        {
            var sigText = GetStr(payload, "signature_text", "signatureText");
            if (sigText.Length == 0)
            {
                await WriteJson(res, 400, new { error = "signature_text is required." }).ConfigureAwait(false);
                return;
            }
            var opt = record["optional"]!.AsObject();
            opt["coPresident"] = new JsonObject
            {
                ["printedName"] = "Tommy James Lindsey",
                ["capacity"] = "Co-President (acknowledgment)",
                ["signatureText"] = sigText,
                ["date"] = NonEmpty(GetStr(payload, "date"), DateTime.UtcNow.ToString("yyyy-MM-dd")),
                ["recordedAtUtc"] = DateTime.UtcNow.ToString("O")
            };
            RecordStore.Save(record, _recordOverride);
            await WriteJsonNode(res, 200, RecordStore.PublicRecord(record)).ConfigureAwait(false);
            return;
        }

        if (path == "/api/optional/justice")
        {
            var sigText = GetStr(payload, "signature_text", "signatureText");
            if (sigText.Length == 0)
            {
                await WriteJson(res, 400, new { error = "signature_text is required." }).ConfigureAwait(false);
                return;
            }
            var opt = record["optional"]!.AsObject();
            opt["justice"] = new JsonObject
            {
                ["printedName"] = "Ramon Santiago IV",
                ["capacity"] = "Justice of Democracy",
                ["signatureText"] = sigText,
                ["date"] = NonEmpty(GetStr(payload, "date"), DateTime.UtcNow.ToString("yyyy-MM-dd")),
                ["recordedAtUtc"] = DateTime.UtcNow.ToString("O")
            };
            RecordStore.Save(record, _recordOverride);
            await WriteJsonNode(res, 200, RecordStore.PublicRecord(record)).ConfigureAwait(false);
            return;
        }

        if (path == "/api/optional/witness")
        {
            var printed = GetStr(payload, "printed_name", "printedName");
            var sigText = GetStr(payload, "signature_text", "signatureText");
            if (printed.Length == 0 || sigText.Length == 0)
            {
                await WriteJson(res, 400, new { error = "printed_name and signature_text are required." }).ConfigureAwait(false);
                return;
            }
            var opt = record["optional"]!.AsObject();
            opt["witness"] = new JsonObject
            {
                ["printedName"] = printed,
                ["signatureText"] = sigText,
                ["date"] = NonEmpty(GetStr(payload, "date"), DateTime.UtcNow.ToString("yyyy-MM-dd")),
                ["recordedAtUtc"] = DateTime.UtcNow.ToString("O")
            };
            RecordStore.Save(record, _recordOverride);
            await WriteJsonNode(res, 200, RecordStore.PublicRecord(record)).ConfigureAwait(false);
            return;
        }

        if (path == "/api/optional/notary")
        {
            var printed = GetStr(payload, "printed_name", "printedName");
            var sigText = GetStr(payload, "signature_text", "signatureText");
            var commission = GetStr(payload, "commission_expires", "commissionExpires");
            var county = GetStr(payload, "county");
            if (printed.Length == 0 || sigText.Length == 0)
            {
                await WriteJson(res, 400, new { error = "printed_name and signature_text are required." }).ConfigureAwait(false);
                return;
            }
            var opt = record["optional"]!.AsObject();
            opt["notary"] = new JsonObject
            {
                ["printedName"] = printed,
                ["signatureText"] = sigText,
                ["commissionExpires"] = commission.Length > 0 ? commission : null,
                ["county"] = county.Length > 0 ? county : null,
                ["date"] = NonEmpty(GetStr(payload, "date"), DateTime.UtcNow.ToString("yyyy-MM-dd")),
                ["recordedAtUtc"] = DateTime.UtcNow.ToString("O")
            };
            RecordStore.Save(record, _recordOverride);
            await WriteJsonNode(res, 200, RecordStore.PublicRecord(record)).ConfigureAwait(false);
            return;
        }

        await WriteJson(res, 404, new { error = "not found" }).ConfigureAwait(false);
    }

    private static string GetStr(JsonObject payload, params string[] keys)
    {
        foreach (var key in keys)
        {
            if (payload[key] is JsonValue v)
            {
                var s = v.GetValue<string?>();
                if (s != null)
                    return s.Trim();
            }
        }
        return "";
    }

    private static string NonEmpty(string value, string fallback) => value.Length > 0 ? value : fallback;

    private static string MimeFromPath(string path)
    {
        return Path.GetExtension(path).ToLowerInvariant() switch
        {
            ".html" => "text/html; charset=utf-8",
            ".css" => "text/css; charset=utf-8",
            ".js" => "text/javascript; charset=utf-8",
            ".json" => "application/json; charset=utf-8",
            ".md" => "text/markdown; charset=utf-8",
            ".png" => "image/png",
            ".svg" => "image/svg+xml",
            _ => "application/octet-stream"
        };
    }

    private static async Task WriteFile(HttpListenerResponse res, string path, string contentType)
    {
        var bytes = await File.ReadAllBytesAsync(path).ConfigureAwait(false);
        await WriteBytes(res, 200, bytes, contentType).ConfigureAwait(false);
    }

    private static async Task WriteJson(HttpListenerResponse res, int status, object payload)
    {
        var bytes = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(payload, JsonUtil.Options));
        await WriteBytes(res, status, bytes, "application/json; charset=utf-8").ConfigureAwait(false);
    }

    private static async Task WriteJsonNode(HttpListenerResponse res, int status, JsonNode node)
    {
        var bytes = Encoding.UTF8.GetBytes(node.ToJsonString(JsonUtil.Options));
        await WriteBytes(res, status, bytes, "application/json; charset=utf-8").ConfigureAwait(false);
    }

    private static async Task WriteBytes(HttpListenerResponse res, int status, byte[] bytes, string contentType, string? disposition = null)
    {
        res.StatusCode = status;
        res.ContentType = contentType;
        res.ContentLength64 = bytes.Length;
        res.Headers["Cache-Control"] = "no-store";
        if (disposition != null)
            res.Headers["Content-Disposition"] = disposition;
        await res.OutputStream.WriteAsync(bytes).ConfigureAwait(false);
        res.OutputStream.Close();
    }
}

internal static class SelfTest
{
    public static int Run()
    {
        var testDir = Path.Combine(Path.GetTempPath(), "piedonian-civic-selftest-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(testDir);
        var testFile = Path.Combine(testDir, "civic_signatures.json");
        try
        {
            var www = FindWwwRoot();
            var content = FindContentRoot();
            var server = new LocalServer(www, content, testFile);
            server.Start(18900);
            try
            {
                using var client = new HttpClient { BaseAddress = new Uri(server.Url) };

                var meta = client.GetStringAsync("/api/meta").GetAwaiter().GetResult();
                if (!meta.Contains(AppConstants.FoundingName, StringComparison.Ordinal))
                    throw new Exception("meta missing founding name");

                var doc = client.GetStringAsync("/api/document").GetAwaiter().GetResult();
                if (!doc.Contains("Constitution of the Piedonian Woods", StringComparison.Ordinal))
                    throw new Exception("combined document missing constitution");
                if (!doc.Contains("Professional Signature Packet", StringComparison.Ordinal) &&
                    !doc.Contains("Signature Packet", StringComparison.Ordinal))
                    throw new Exception("combined document missing signature packet");

                var recJson = client.GetStringAsync("/api/record").GetAwaiter().GetResult();
                using (var docNode = JsonDocument.Parse(recJson))
                {
                    if (docNode.RootElement.GetProperty("founding").GetProperty("status").GetString() != "open")
                        throw new Exception("founding should start open");
                }

                // wrong name rejected
                var bad = client.PostAsync("/api/founding",
                    new StringContent(JsonSerializer.Serialize(new { signature_text = "Wrong Name" }), Encoding.UTF8, "application/json"))
                    .GetAwaiter().GetResult();
                if ((int)bad.StatusCode != 400)
                    throw new Exception("expected 400 for wrong founding name");

                var ok = client.PostAsync("/api/founding",
                    new StringContent(JsonSerializer.Serialize(new { signature_text = AppConstants.FoundingName }), Encoding.UTF8, "application/json"))
                    .GetAwaiter().GetResult();
                ok.EnsureSuccessStatusCode();
                var closedBody = ok.Content.ReadAsStringAsync().GetAwaiter().GetResult();
                using (var closedDoc = JsonDocument.Parse(closedBody))
                {
                    var status = closedDoc.RootElement.GetProperty("founding").GetProperty("status").GetString();
                    if (status != "closed")
                        throw new Exception("founding not closed");
                }

                var again = client.PostAsync("/api/founding",
                    new StringContent(JsonSerializer.Serialize(new { signature_text = AppConstants.FoundingName }), Encoding.UTF8, "application/json"))
                    .GetAwaiter().GetResult();
                if ((int)again.StatusCode != 409)
                    throw new Exception("expected 409 on second founding signature");

                foreach (var name in new[] { "Alice Citizen", "Bob Citizen" })
                {
                    var body = JsonSerializer.Serialize(new
                    {
                        printed_name = name,
                        granted_by = AppConstants.FoundingName,
                        granted_date = "2026-08-10",
                        signed_date = "2026-08-10",
                        signature_text = name
                    });
                    var c = client.PostAsync("/api/citizen", new StringContent(body, Encoding.UTF8, "application/json"))
                        .GetAwaiter().GetResult();
                    c.EnsureSuccessStatusCode();
                }

                var final = client.GetStringAsync("/api/record").GetAwaiter().GetResult();
                using (var finalDoc = JsonDocument.Parse(final))
                {
                    var count = finalDoc.RootElement.GetProperty("citizens").GetArrayLength();
                    if (count != 2)
                        throw new Exception("expected 2 citizens");
                }

                var md = client.GetStringAsync("/api/export.md").GetAwaiter().GetResult();
                if (!md.Contains("Alice Citizen", StringComparison.Ordinal) ||
                    !md.Contains("FOUNDING SIGNATURE CLOSED", StringComparison.Ordinal))
                    throw new Exception("export markdown incomplete");

                Console.WriteLine("SELF-TEST OK");
                return 0;
            }
            finally
            {
                server.Stop();
            }
        }
        finally
        {
            try { Directory.Delete(testDir, recursive: true); } catch { /* ignore */ }
        }
    }

    public static string FindWwwRoot()
    {
        var candidates = new[]
        {
            Paths.WwwRoot,
            Path.GetFullPath(Path.Combine(Paths.AppRoot, "wwwroot")),
            Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "wwwroot")),
            Path.GetFullPath(Path.Combine(Environment.CurrentDirectory, "wwwroot")),
            Path.GetFullPath(Path.Combine(Environment.CurrentDirectory, "PiedonianCivicDocument", "wwwroot")),
        };
        foreach (var c in candidates)
        {
            if (Directory.Exists(c) && File.Exists(Path.Combine(c, "index.html")))
                return c;
        }
        throw new DirectoryNotFoundException("wwwroot not found");
    }

    public static string FindContentRoot()
    {
        var candidates = new[]
        {
            Paths.ContentRoot,
            Path.GetFullPath(Path.Combine(Paths.AppRoot, "Content")),
            Path.GetFullPath(Path.Combine(Environment.CurrentDirectory, "Content")),
            Path.GetFullPath(Path.Combine(Environment.CurrentDirectory, "PiedonianCivicDocument", "Content")),
            Path.GetFullPath(Path.Combine(Environment.CurrentDirectory)),
        };
        foreach (var c in candidates)
        {
            if (File.Exists(Path.Combine(c, "PIEDONIAN_COMBINED_CIVIC_DOCUMENT.md")))
                return c;
        }
        throw new DirectoryNotFoundException("Content root not found");
    }
}

public static class Program
{
    public static int Main(string[] args)
    {
        if (args.Any(a => a is "--self-test" or "self-test"))
            return SelfTest.Run();

        var www = SelfTest.FindWwwRoot();
        var content = SelfTest.FindContentRoot();
        var server = new LocalServer(www, content);
        server.Start();

        Console.WriteLine(AppConstants.AppName);
        Console.WriteLine($"Open: {server.Url}");
        Console.WriteLine($"Data: {Paths.RecordFile}");
        Console.WriteLine("Combined document + electronic signature UI for Windows 11.");
        Console.WriteLine("Press Ctrl+C to stop.");

        if (!args.Any(a => a is "--no-browser" or "no-browser"))
        {
            try
            {
                var psi = new System.Diagnostics.ProcessStartInfo
                {
                    FileName = server.Url,
                    UseShellExecute = true
                };
                System.Diagnostics.Process.Start(psi);
            }
            catch
            {
                // Browser open is best-effort
            }
        }

        var quit = new ManualResetEventSlim(false);
        Console.CancelKeyPress += (_, e) =>
        {
            e.Cancel = true;
            quit.Set();
        };
        quit.Wait();
        Console.WriteLine("Shutting down...");
        server.Stop();
        return 0;
    }
}
