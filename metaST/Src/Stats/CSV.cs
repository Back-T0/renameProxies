using Core.Meta;

namespace Stats;

public class CSV
{
    public static string Generate(List<ProxyNode> proxies)
    {
        Dictionary<string, Func<ProxyNode, string>> cols = new(){
            { "name",       (proxy) => $"{proxy.Name}"                   },
            { "type",       (proxy) => $"{proxy.Type}"                   },
            { "delay(ms)",  (proxy) => $"{proxy.DelayResult.Result():0}" },
            { "speed(bps)", (proxy) => $"{proxy.SpeedResult.Result():0}" },
            { "ip",         (proxy) => $"{proxy.GeoInfo.Address}"        },
            { "country",    (proxy) => $"{proxy.GeoInfo.CountryCode}"    },
            { "isp",        (proxy) => $"{proxy.GeoInfo.Organization}"   },
        };

        string header = string.Join(",", cols.Select(col => col.Key).ToList());
        string body = string.Join(Environment.NewLine,
            proxies.Select(proxy => string.Join(",",
                cols.Select(col => col.Value(proxy))
                .Select(val => $"\"{val.Replace("\"", "\"\"")}\"").ToList()
            )));
        return $"{header}{Environment.NewLine}{body}";
    }
}