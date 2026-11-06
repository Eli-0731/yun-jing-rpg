// 青溪水工 B：小型 JSON 讀寫（保留物件鍵的順序，規則比對要和 JS 的物件順序一致）。
// 物件 → JObj，陣列 → List<object>，數字 → double，字串、bool、null 原樣。
using System.Collections.Generic;
using System.Globalization;
using System.Text;

public class JObj
{
    public readonly List<string> Keys = new List<string>();
    readonly Dictionary<string, object> map = new Dictionary<string, object>();
    public object this[string k]
    {
        get => map.TryGetValue(k, out var v) ? v : null;
        set { if (!map.ContainsKey(k)) Keys.Add(k); map[k] = value; }
    }
    public bool Has(string k) => map.ContainsKey(k);
    public void Remove(string k) { if (map.Remove(k)) Keys.Remove(k); }
    public JObj O(string k) => this[k] as JObj;
    public List<object> A(string k) => this[k] as List<object>;
    public string S(string k) => this[k] as string;
    public double D(string k) => this[k] is double d ? d : 0;
}

public static class MiniJson
{
    public static object Parse(string s) { int i = 0; var v = Value(s, ref i); return v; }

    static void Ws(string s, ref int i) { while (i < s.Length && char.IsWhiteSpace(s[i])) i++; }

    static object Value(string s, ref int i)
    {
        Ws(s, ref i);
        char c = s[i];
        if (c == '{')
        {
            var o = new JObj(); i++; Ws(s, ref i);
            if (s[i] == '}') { i++; return o; }
            while (true)
            {
                Ws(s, ref i); var k = Str(s, ref i); Ws(s, ref i); i++;   // ':'
                o[k] = Value(s, ref i); Ws(s, ref i);
                if (s[i++] == '}') return o;
            }
        }
        if (c == '[')
        {
            var a = new List<object>(); i++; Ws(s, ref i);
            if (s[i] == ']') { i++; return a; }
            while (true)
            {
                a.Add(Value(s, ref i)); Ws(s, ref i);
                if (s[i++] == ']') return a;
            }
        }
        if (c == '"') return Str(s, ref i);
        if (s.Substring(i).StartsWith("true")) { i += 4; return true; }
        if (s.Substring(i).StartsWith("false")) { i += 5; return false; }
        if (s.Substring(i).StartsWith("null")) { i += 4; return null; }
        int st = i;
        while (i < s.Length && "+-0123456789.eE".IndexOf(s[i]) >= 0) i++;
        return double.Parse(s.Substring(st, i - st), CultureInfo.InvariantCulture);
    }

    static string Str(string s, ref int i)
    {
        var sb = new StringBuilder(); i++;
        while (s[i] != '"')
        {
            if (s[i] == '\\')
            {
                i++;
                switch (s[i])
                {
                    case 'n': sb.Append('\n'); break;
                    case 't': sb.Append('\t'); break;
                    case 'r': sb.Append('\r'); break;
                    case 'u': sb.Append((char)int.Parse(s.Substring(i + 1, 4), NumberStyles.HexNumber)); i += 4; break;
                    default: sb.Append(s[i]); break;
                }
            }
            else sb.Append(s[i]);
            i++;
        }
        i++;
        return sb.ToString();
    }

    public static string Quote(string s)
    {
        var sb = new StringBuilder("\"");
        foreach (var ch in s)
        {
            if (ch == '"' || ch == '\\') sb.Append('\\').Append(ch);
            else if (ch == '\n') sb.Append("\\n");
            else sb.Append(ch);
        }
        return sb.Append('"').ToString();
    }
}
