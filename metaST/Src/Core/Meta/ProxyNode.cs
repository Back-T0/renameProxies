using System.Collections.Concurrent;
using System.Net;
using Core.CommandLine;
using Core.CommandLine.Enum;
using Core.Geo;
using Core.Test.Reuslt;
using Util;

namespace Core.Meta;
public class ProxyNode(Dictionary<dynamic, dynamic> info)
{
    public override bool Equals(object? obj)
    {
        return obj != null && GetHashCode() == obj.GetHashCode();
    }

    public override int GetHashCode()
    {
        return Type.GetHashCode() ^ Name.GetHashCode() ^ Port.GetHashCode();
    }

    public Dictionary<dynamic, dynamic> Info { get; set; } = info;

    public string Name
    {
        get { return Info["name"]; }
        set { Info["name"] = value; }
    }

    public string Type
    {
        get { return Info["type"]; }
        set { Info["type"] = value; }
    }
    public string Server
    {
        get { return Info["server"]; }
        set { Info["server"] = value; }
    }

    public string Port
    {
        get { return Info["port"]; }
        set { Info["port"] = value; }
    }

    public IWebProxy? Mixed { get; set; }

    public DelayResult DelayResult { get; set; } = new();

    public SpeedResult SpeedResult { get; set; } = new();

    public GeoInfo GeoInfo { get; set; } = new();

    public static List<ProxyNode> Distinct(List<ProxyNode> proxies)
    {
        Logger.Info("开始节点去重...");
        // 去重（协议类型 + 服务器 + 端口）
        proxies = proxies.Where(proxy => proxy.Info.ContainsKey("type") && proxy.Info.ContainsKey("server") && proxy.Info.ContainsKey("port")).ToList();
        proxies = proxies.DistinctBy((proxy) => string.Join('_', [proxy.Type, proxy.Server, proxy.Port])).ToList();
        // 名称重复的添加序号后缀
        proxies = proxies
            .GroupBy(p => p.Name)
            .SelectMany(grp => grp.Select((p, i) =>
            {
                p.Name = grp.Count() > 1 ? $"{p.Name}_{i + 1}" : p.Name;
                return p;
            })).ToList();
        Logger.Info($"节点去重完成,剩余{proxies.Count}个节点");
        return proxies;
    }

    public static List<ProxyNode> Rename(List<ProxyNode> proxies)
    {
        CommandLineOptions options = Context.Options;
        if (proxies != null && proxies.Count > 0)
        {
            // 查询GEO信息重命名
            if (options.GeoLookup ?? true)
            {
                Logger.Info("开始查询GEO信息...");
                ConcurrentDictionary<IWebProxy, GeoInfo> infoMap = [];
                int chunkIndex = 0;
                foreach (ProxyNode[] chunk in proxies.Chunk(Constants.MaxPortsOccupied))
                {
                    // 查询GEO信息
                    MetaService.UsingProxies([.. chunk], proxied =>
                    {
                        return proxied.AsParallel().AsOrdered().WithDegreeOfParallelism(Environment.ProcessorCount).Select((proxy, index) =>
                        {
                            GeoInfo geoInfo = Task.Run(() => GeoElector.LookupAsnyc(proxy.Mixed)).Result;
                            infoMap.TryAdd(proxy.Mixed ??= new WebProxy(), geoInfo);
                            int current = chunkIndex * Constants.MaxPortsOccupied + index + 1;
                            Logger.Info(Strings.Padding(Emoji.EmojiToShort($"[{current}/{proxies.Count}] {proxy.Name}"), Constants.MaxSubject) + " ==> " + $"{geoInfo.CountryCode}");
                            return geoInfo;
                        }).ToList();
                    });
                    chunkIndex += 1;
                }

                // 分配GEO信息
                proxies.ForEach((proxy) =>
                {
                    proxy.GeoInfo = proxy.Mixed != null && infoMap.TryGetValue(proxy.Mixed, out var geoInfo) ? geoInfo : new();
                });
                Logger.Info("查询GEO信息完成");
            }
            // 节点重命名
            proxies.ForEach(proxy =>
            {
                List<string?> frozen = [
                    (options.GeoLookup??true) ? proxy.GeoInfo.Emoji : string.Empty
                ];
                List<string?> unfrozen = [
                    !string.IsNullOrWhiteSpace(options.Tag) ? options.Tag : string.Empty,
                    proxy.GeoInfo.Country
                ];
                string frozenPart = string.Join("_", frozen.Where(str => !string.IsNullOrWhiteSpace(str)).ToList());
                string unfrozenPart = string.Join("_", unfrozen.Where(str => !string.IsNullOrWhiteSpace(str)).ToList());
                proxy.Name = $"{frozenPart} {unfrozenPart}";
            });
            // 重名添加序号
            if (proxies.Select(proxy => proxy.Name).Distinct().Count() != proxies.Count)
            {
                proxies = Distinct(proxies);
                proxies = Sort(proxies);        // Distinct会按照分组排序
            }
        }
        return proxies ?? [];
    }

    public static List<ProxyNode> Purify(List<ProxyNode> proxies)
    {
        List<ProxyNode> purified = [];
        int chunkIndex = 0;
        foreach (ProxyNode[] chunk in proxies.Chunk(Constants.MaxPortsOccupied))
        {
            purified.AddRange(BinaryTest([.. chunk]));
            Logger.Info(Strings.Padding($"[{chunkIndex * Constants.MaxPortsOccupied + chunk.Length}/{proxies.Count}]", Constants.MaxSubject) + " 节点配置校验...");
            chunkIndex += 1;
        }
        if (purified.Count < proxies.Count)
        {
            Logger.Warn($"节点配置校验完成,排除{proxies.Count - purified.Count}个节点");
        }
        else
        {
            Logger.Info("节点配置校验完成");
        }
        return purified;
    }

    private static List<ProxyNode> BinaryTest(List<ProxyNode> proxies)
    {
        if (proxies != null && proxies.Count > 0)
        {
            try
            {
                return MetaService.UsingProxies(proxies, (proxied) => proxies);
            }
            catch
            {
                return proxies.Count > 1 ? [.. BinaryTest(proxies.Take(proxies.Count / 2).ToList()), .. BinaryTest(proxies.Skip(proxies.Count / 2).ToList())] : [];
            }
        }
        return [];
    }

    public static List<ProxyNode> Sort(List<ProxyNode> proxies)
    {
        CommandLineOptions options = Context.Options;
        if (SortPreference.delay.Equals(options.SortPreference) && (options.DelayTestEnable ?? true))
        {
            Logger.Info("节点排序: 延迟升序");
            return [.. proxies.OrderBy((proxy) => proxy.DelayResult.Result())];
        }
        if (SortPreference.speed.Equals(options.SortPreference) && (options.SpeedTestEnable ?? false))
        {
            Logger.Info("节点排序: 下载速度降序");
            return [.. proxies.OrderByDescending((proxy) => proxy.SpeedResult.Result())];
        }
        return proxies;
    }

    public static List<ProxyNode> Truncate(List<ProxyNode> proxies)
    {
        if (Context.Options.Top > 0 && proxies != null && proxies.Count > 0)
        {
            Logger.Info($"截取前{Context.Options.Top}条配置");
            return proxies.Take(Context.Options.Top).ToList();
        }
        return proxies ?? [];
    }
}