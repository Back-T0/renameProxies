using CommandLine;
using Core.CommandLine.Enum;

namespace Core.CommandLine;
public class CommandLineOptions
{
    [Option("config", Required = true, HelpText = "clash配置文件路径(或链接地址)")]
    public required string Config { get; set; }

    [Option("proxy", Required = false, HelpText = "资源下载代理(http://host:port)")]
    public required string Porxy { get; set; }

    [Option("de", Required = false, Default = true, HelpText = "是否进行延迟测试")]
    public required bool? DelayTestEnable { get; set; }

    [Option("du", Required = false, Default = "https://www.google.com/gen_204", HelpText = "延迟测试链接")]
    public required string DelayTestUrl { get; set; }

    [Option("dt", Required = false, Default = 1000, HelpText = "延迟测试超时(ms)")]
    public required int DelayTestTimeout { get; set; }

    [Option("dn", Required = false, Default = 16, HelpText = "延迟测试线程数量")]
    public required int DelayTestThreads { get; set; }

    [Option("dr", Required = false, Default = 4, HelpText = "延迟测试轮数")]
    public required int DelayTestRounds { get; set; }

    [Option("df", Required = false, Default = 1000, HelpText = "延迟测试过滤阈值(ms)")]
    public required double DelayTestFilter { get; set; }

    [Option("se", Required = false, Default = false, HelpText = "是否进行下载测试")]
    public required bool? SpeedTestEnable { get; set; }

    [Option("su", Required = false, Default = "https://cdn.cloudflare.steamstatic.com/steam/apps/256843155/movie_max.mp4", HelpText = "下载测试链接")]
    public required string SpeedTestUrl { get; set; }

    [Option("st", Required = false, Default = 5000, HelpText = "下载测试连接超时(ms)")]
    public required int SpeedTestTimeout { get; set; }

    [Option("sd", Required = false, Default = 10 * 1000, HelpText = "下载测试时长(ms)")]
    public required int SpeedTestDuration { get; set; }

    [Option("sr", Required = false, Default = 1, HelpText = "下载测试测试轮数")]
    public required int SpeedTestRounds { get; set; }

    [Option("sf", Required = false, Default = 1000 * 1024 * 8, HelpText = "下载测试过滤阈值(bps)")]
    public required double SpeedTestFilter { get; set; }

    [Option("ff", Required = false, Default = 0.5, HelpText = "快速失败比率(测试一定比率仍无结果,直接失败)")]
    public required double FailFastRatio { get; set; }

    [Option("sort", Required = false, Default = SortPreference.delay, HelpText = "结果排序偏好")]
    public required SortPreference SortPreference { get; set; }

    [Option("top", Required = false, HelpText = "结果截选前若干条")]
    public int Top { get; set; }

    [Option("tag", Required = false, HelpText = "节点命名前缀")]
    public string Tag { get; set; } = string.Empty;

    [Option("geo", Required = false, Default = true, HelpText = "是否GEO查询并重命名")]
    public required bool? GeoLookup { get; set; }

    [Option("gt", Required = false, Default = 10 * 1000, HelpText = "GEO查询超时(ms)")]
    public required int GeoLookupTimeout { get; set; }

    [Option("group", Required = false, Default = GroupType.regieon, HelpText = "代理组类型")]
    public required GroupType GroupType { get; set; }

    [Option("icon", Required = false, Default = IconType.http, HelpText = "图标类型")]
    public required IconType IconType { get; set; }

    [Option("ruleset", Required = false, Default = RuleSet.loyalsoldier, HelpText = "结果配置文件使用的规则集")]
    public required RuleSet RuleSet { get; set; }

    [Option("mirror", Required = false, Default = "https://mirror.ghproxy.com/", HelpText = "Github资源镜像加速地址")]
    public required string GithubMirror { get; set; }

    [Option("output", Required = false, HelpText = "输出路径/文件名")]
    public string? Output { get; set; }

    [Option("verbose", Required = false, Default = false, HelpText = "显示详细输出")]
    public required bool Verbose { get; set; }

    [Option("pause", Required = false, Default = false, HelpText = "程序结束后等待")]
    public required bool Pause { get; set; }
}