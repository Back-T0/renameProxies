
namespace Core.Geo.Lookup;

public class IPDataCloud : AJsonLookup
{
    public override LookupType Type() => LookupType.GEO;

    protected override HttpRequestMessage SelfRequestMessage()
    {
        return new()
        {
            Method = HttpMethod.Get,
            RequestUri = new Uri("https://api.ipdatacloud.com/v3/query?key=69bb0813cf9f11eeb09400163e25360e"),
            Headers =
            {
                { "Accept-Language",  "en-US" },
                { "Referer", "https://www.ipdatacloud.com/" }
            }
        };
    }
    protected override ResultMapping SelfResultMapping()
    {
        return new ResultMapping()
        {
            AddressField = "data.ip",
            CountryCodeField = "data.country_code",
            CountryField = "_CountryField",
            OrganizationField = "data.isp"
        };
    }

    protected override HttpRequestMessage AddressRequestMessage(string address)
    {
        return new()
        {
            Method = HttpMethod.Get,
            RequestUri = new Uri($"https://api.ipdatacloud.com/v3/query?ip={address}&key=69bb0813cf9f11eeb09400163e25360e"),
            Headers = {
                { "Accept-Language",  "en-US" },
                { "Referer", "https://www.ipdatacloud.com/" }
            }
        };
    }
    protected override ResultMapping AddressResultMapping() => SelfResultMapping();
}