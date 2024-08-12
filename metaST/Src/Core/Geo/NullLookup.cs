using System.Net;

namespace Core.Geo;
public class NullLookup : AGeoLookup
{
    public override bool Enabled() => false;

    public override GeoInfo Lookup(IWebProxy? proxy)
    {
        throw new NotImplementedException();
    }

    public override GeoInfo Lookup(IWebProxy? proxy, string address)
    {
        throw new NotImplementedException();
    }

    public override LookupType Type()
    {
        throw new NotImplementedException();
    }
}