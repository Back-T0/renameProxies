using System.Net;

namespace Core.Geo;

public abstract class AGeoLookup
{
    // 查询类型
    public abstract LookupType Type();
    // GEO查询实现
    public abstract GeoInfo Lookup(IWebProxy? proxy);
    public abstract GeoInfo Lookup(IWebProxy? proxy, string address);
    // 是否启用
    public virtual bool Enabled() => true;
    // 置信度
    public virtual double Confidence() => 1.0;
    // 查询超时
    public double LookupTimout { get; set; } = 30 * 1000;

    // 查询类型枚举
    public enum LookupType { IP, GEO, BOTH }
}