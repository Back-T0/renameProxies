
namespace Core.Geo.Lookup;

public class IPGeoLocation : AJsonLookup
{
    public override LookupType Type() => LookupType.GEO;

    protected override HttpRequestMessage SelfRequestMessage()
    {
        return new()
        {
            Method = HttpMethod.Get,
            RequestUri = new Uri("https://api.ipgeolocation.io/ipgeo"),
            Headers =
            {
                { "Accept-Language",  "en-US" },
                { "Referer", "https://ipgeolocation.io" }
            }
        };
    }
    protected override ResultMapping SelfResultMapping()
    {
        return new ResultMapping()
        {
            AddressField = "ip",
            CountryCodeField = "country_code2",
            CountryField = "country_name",
            OrganizationField = "isp"
        };
    }

    protected override HttpRequestMessage AddressRequestMessage(string address)
    {
        return new()
        {
            Method = HttpMethod.Get,
            RequestUri = new Uri($"https://api.ipgeolocation.io/ipgeo?ip={address}"),
            Headers = {
                { "Accept-Language",  "en-US" },
                { "Referer", "https://ipgeolocation.io/" }
            }
        };
    }
    protected override ResultMapping AddressResultMapping() => SelfResultMapping();
}