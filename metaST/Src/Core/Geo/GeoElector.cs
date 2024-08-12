using System.Net;
using System.Reflection;
using Util;
using static Core.Geo.AGeoLookup;

namespace Core.Geo;
public class GeoElector
{
    // 支持查询当前连接GEO信息的实现
    private static readonly List<AGeoLookup> selfLookups;
    // 支持根据IP查询GEO信息的实现
    private static readonly List<AGeoLookup> addressLookups;
    static GeoElector()
    {
        List<AGeoLookup> instances = [];
        // 查询所有的AGeoLookup实现(非接口类、非抽象类、非内部类)
        List<Type> types = Assembly.GetExecutingAssembly().GetTypes()
            .Where(type => type.IsAssignableTo(typeof(AGeoLookup)))
            .Where(type => !type.IsInterface && !type.IsAbstract && type.DeclaringType == null)
            .ToList();
        // 创建实例对象
        foreach (Type type in types)
        {
            try
            {
                object? instance = Activator.CreateInstance(type);
                if (instance != null) instances.Add((AGeoLookup)instance);
            }
            catch
            {
                Logger.Error($"Error creating GeoLookup instance: {type.Name}");
            }
        }
        // 排除掉未启用的
        instances = instances.Where(instance => instance.Enabled()).ToList();
        // 设置查询超时
        instances.ForEach(instance => instance.LookupTimout = Context.Options.GeoLookupTimeout);
        // 分配实例对象
        selfLookups = instances.Where(instance => new LookupType[] { LookupType.BOTH, LookupType.IP }.Contains(instance.Type())).ToList();
        addressLookups = instances.Where(instance => new LookupType[] { LookupType.BOTH, LookupType.GEO }.Contains(instance.Type())).ToList();
    }

    public static Task<GeoInfo> LookupAsnyc(IWebProxy? proxy)
    {
        return Task.Run(() =>
        {
            // 查询IP信息
            List<GeoInfo> ips = [];
            Task.WaitAll(selfLookups.Select((instance) => Task.Run(() => ips.Add(instance.Lookup(proxy)))).ToArray());
            // 选举IP信息
            string address = Elect(ips, (info) => info.Address, (key) => !string.IsNullOrWhiteSpace(key));
            if (!string.IsNullOrWhiteSpace(address))
            {
                // 查询GEO信息
                List<GeoInfo> geos = [];
                Task.WaitAll(addressLookups.Select((instance) => Task.Run(() => geos.Add(instance.Lookup(proxy, address)))).ToArray());
                // 选举GEO信息
                string countryCode = Elect(geos, (info) => info.CountryCode, key => !string.IsNullOrWhiteSpace(key) && !"UNKNOWN".Equals(key), "UNKNOWN");
                string country = Elect(geos, (info) => info.Country, key => !string.IsNullOrWhiteSpace(key));
                string organization = Elect(geos, (info) => info.Organization, key => !string.IsNullOrWhiteSpace(key));
                return new GeoInfo(new NullLookup(), address, countryCode, country, organization, proxy);
            }
            return new();
        });
    }

    private static string Elect(IEnumerable<GeoInfo> infos, Func<GeoInfo, string> groupBy, Predicate<string>? filter = null, string defaultValue = "")
    {
        string? elected = infos
            .GroupBy(groupBy)
            // 置信度从高到低排序
            .OrderByDescending(group => group.ToList().Select(info => info.GeoLookup.Confidence()).Sum())
            .Select(group => group.Key)
            .FirstOrDefault(key => filter == null || filter.Invoke(key));
        return elected ?? defaultValue;
    }
}