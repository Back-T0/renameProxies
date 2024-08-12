using System.Net;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using Util;

namespace Core.Geo;

public delegate void AttributesApplier<E, V>(E geoInfo, V? val);

public abstract class AJsonLookup : AGeoLookup
{
    public override GeoInfo Lookup(IWebProxy? proxy) => DoLookup(proxy, string.Empty);

    public override GeoInfo Lookup(IWebProxy? proxy, string address) => DoLookup(proxy, address);

    protected GeoInfo DoLookup(IWebProxy? proxy, string address)
    {
        // 是否根据已知的IP地址查询
        bool addressLookup = !string.IsNullOrWhiteSpace(address);

        GeoInfo geoInfo = new() { GeoLookup = this };
        // 读取JSON串
        string? json = HttpRequest.UsingHttpClient((client) =>
        {
            try
            {
                HttpRequestMessage message = addressLookup ? AddressRequestMessage(address) : SelfRequestMessage();
                HttpResponseMessage response = client.SendAsync(message).Result;
                response.EnsureSuccessStatusCode();
                return response.Content.ReadAsStringAsync().Result;
            }
            catch (Exception ex)
            {
                if (typeof(AggregateException).Equals(ex.GetType()))
                {
                    while (ex.InnerException != null) ex = ex.InnerException;
                }
                Logger.Debug($"Error looking up Geo via {GetType().Name}: {ex.Message}");
                return string.Empty;
            }
        }, LookupTimout, proxy);

        // 尝试直连查询已知IP的GEO信息
        if (addressLookup && string.IsNullOrWhiteSpace(json) && proxy != null) return DoLookup(null, address);

        // JSON串预处理
        json = JsonPreprocess(json);
        // 提取JSON串中属性并赋值
        if (!string.IsNullOrWhiteSpace(json))
        {
            ResultMapping mapping = addressLookup ? AddressResultMapping() : SelfResultMapping();
            ParseAndApply(geoInfo, json, new Dictionary<string, AttributesApplier<GeoInfo, string?>>()
            {
                { mapping.AddressField,      (info, val) => info.Address = val ?? string.Empty      },
                { mapping.CountryCodeField,  (info, val) => info.CountryCode = val ?? "UNKNOWN"     },
                { mapping.CountryField,      (info, val) => info.Country = val ?? string.Empty      },
                { mapping.OrganizationField, (info, val) => info.Organization = val ?? string.Empty }
            });
        }
        return geoInfo;
    }

    protected abstract HttpRequestMessage SelfRequestMessage();
    protected abstract HttpRequestMessage AddressRequestMessage(string address);
    protected virtual string? JsonPreprocess(string? json) => json;
    protected abstract ResultMapping SelfResultMapping();
    protected abstract ResultMapping AddressResultMapping();
    // 结果字段映射
    protected class ResultMapping
    {
        public string AddressField { get; set; } = "_AddressField";
        public string CountryCodeField { get; set; } = "_CountryCodeField";
        public string CountryField { get; set; } = "_CountryField";
        public string OrganizationField { get; set; } = "_OrganizationField";
    }
    private static void ParseAndApply(GeoInfo geoInfo, string? json, Dictionary<string, AttributesApplier<GeoInfo, string?>> actions)
    {
        if (!string.IsNullOrWhiteSpace(json))
        {
            try
            {
                JObject? jObject = JsonConvert.DeserializeObject<JObject>(json);
                if (jObject != null)
                {
                    foreach (var action in actions)
                    {
                        JToken? tmp = jObject;
                        if (!string.IsNullOrWhiteSpace(action.Key))
                        {
                            string[] keys = action.Key.Split('.');
                            foreach (string key in keys)
                            {
                                tmp = tmp?[key];
                            }
                            string? val = tmp?.ToString();
                            action.Value.Invoke(geoInfo, val);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Logger.Debug($"Error parsing Geo JSON: {ex.Message}");
            }
        }
    }
}