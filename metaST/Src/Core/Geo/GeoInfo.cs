using System.Net;

namespace Core.Geo;

public class GeoInfo
{
    public AGeoLookup GeoLookup { get; set; }
    public string Address { get; set; } = string.Empty;
    public string CountryCode { get; set; } = "UNKNOWN";
    public string? _country;
    public string Country
    {
        get
        {
            string? name = !string.IsNullOrWhiteSpace(CountryCode) && CountryCode.Length == 2
            ? CountryNames.Looup(CountryCode) : (string.IsNullOrWhiteSpace(_country) ? string.Empty : _country);
            return string.IsNullOrWhiteSpace(name) ? "未知" : name;
        }
        set { _country = value; }
    }
    public string Organization { get; set; } = string.Empty;
    public string Emoji
    {
        get
        {
            return string.IsNullOrWhiteSpace(CountryCode) || CountryCode.Length != 2 ?
            "❓" : GetEmojiByCode(CountryCode);
        }
    }
    public string Icon
    {
        get
        {
            return string.IsNullOrWhiteSpace(CountryCode) || CountryCode.Length != 2 ?
           GetIconByCode(CountryCode, false) : GetIconByCode(CountryCode, true);
        }
    }
    public IWebProxy? Proxy { get; set; }
    public GeoInfo()
    {
        GeoLookup = new NullLookup();
    }
    public GeoInfo(AGeoLookup geoLookup, string address, string countryCode, string country, string organization, IWebProxy? proxy)
    {
        GeoLookup = geoLookup;
        Address = address;
        CountryCode = countryCode;
        Country = country;
        Organization = organization;
        Proxy = proxy;
    }
    private static string GetEmojiByCode(string countryCode)
    {
        countryCode = countryCode.ToUpper();
        const int offset = 0x1F1E6 - 'A';
        return char.ConvertFromUtf32(countryCode[0] + offset) + char.ConvertFromUtf32(countryCode[1] + offset);
    }
    private static string GetIconByCode(string countryCode, bool flag)
    {
        string fileName = countryCode.ToLower() + ".svg";
        return flag ? "icons.flags." + fileName : "icons." + fileName;
    }
}