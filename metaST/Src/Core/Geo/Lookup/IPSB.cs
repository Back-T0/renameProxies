namespace Core.Geo.Lookup;

public class IPSB : AJsonLookup
{
    public override LookupType Type() => LookupType.BOTH;
    public override double Confidence() => 5.0;

    protected override HttpRequestMessage SelfRequestMessage()
    {
        return new()
        {
            Method = HttpMethod.Get,
            RequestUri = new Uri("https://ipv4.ip.gs/addrinfo"),
            Headers =
            {
                { "Accept-Language",  "en-US" },
                { "Referer", "https://ip.gs/" }
            }
        };
    }
    protected override ResultMapping SelfResultMapping()
    {
        return new ResultMapping()
        {
            AddressField = "address",
            CountryCodeField = "_CountryCodeField",
            CountryField = "country",
            OrganizationField = "isp.name"
        };
    }

    protected override HttpRequestMessage AddressRequestMessage(string address)
    {
        return new()
        {
            Method = HttpMethod.Get,
            RequestUri = new Uri($"https://api.ip.sb/geoip/{address}"),
            Headers =
            {
                { "Accept-Language",  "en-US" },
                { "Referer", "https://ip.gs/api/" }
            }
        };
    }
    protected override ResultMapping AddressResultMapping()
    {
        return new ResultMapping()
        {
            AddressField = "ip",
            CountryCodeField = "country_code",
            CountryField = "country",
            OrganizationField = "organization"
        };
    }
}