using System.Net;
using System.Text;
using System.Text.RegularExpressions;
using Core.CommandLine;
using Core.CommandLine.Enum;
using Util;

namespace Core.Meta.Config;

public class MetaConfig
{
    public static List<ProxyNode> GetConfigProxies(string config, bool includeProxies = true, bool includeProviders = true)
    {
        // 不包含任何节点
        if (!includeProxies && !includeProviders) return [];

        // 订阅链接 或 节点池链接
        if (config.StartsWith("http"))
        {
            try
            {
                Logger.Info("下载配置文件：" + config);
                // 下载获取文件内容
                IWebProxy? proxy = string.IsNullOrEmpty(Context.Options.Porxy) ? null : new WebProxy(Context.Options.Porxy);
                string? content = HttpRequest.UsingHttpClient((client) =>
                {
                    // 设置User-Agent为clash
                    client.DefaultRequestHeaders.Add("User-Agent", "clash");
                    return client.GetAsync(config).Result.Content.ReadAsStringAsync().Result;
                }, 30 * 1000, proxy);
                // 文件内容要求不为空
                if (string.IsNullOrWhiteSpace(content)) throw new Exception(config);
                Logger.Info("下载配置文件完成");
                // 保存到临时目录
                string dest = Path.Combine(Constants.WorkSpaceTemp, Strings.Md5(config) + ".yaml");
                try
                {
                    Files.WriteToFile(new MemoryStream(Encoding.UTF8.GetBytes(content)), dest);
                    return GetConfigProxies(dest, includeProxies, includeProviders);
                }
                finally
                {
                    Files.DeleteFile(dest);
                }
            }
            catch (Exception ex)
            {
                Exception temp = ex;
                while (temp.InnerException != null)
                {
                    temp = temp.InnerException;
                }
                Logger.Warn("下载配置文件失败:" + temp.Message);
                return [];
            }
        }

        // 保存节点列表
        List<ProxyNode> proxyList = [];
        try
        {
            // 解析配置文件
            string yaml = File.ReadAllText(config);
            // 尝试Base64解码
            yaml = Strings.IsBase64String(yaml) ? Strings.Base64Decoding(yaml, Encoding.UTF8) : yaml;

            Dictionary<dynamic, dynamic> yamlObject = YamlDot.DeserializeObject(yaml);
            // 如果存在proxies
            if (includeProxies && yamlObject.ContainsKey("proxies"))
            {
                List<dynamic> proxies = yamlObject["proxies"];
                proxies.ForEach((proxy) => proxyList.Add(new ProxyNode(proxy)));
            }

            // 如果存在proxy-providers
            if (includeProviders && yamlObject.ContainsKey("proxy-providers"))
            {
                Dictionary<dynamic, dynamic> providers = yamlObject["proxy-providers"];
                // 读取provider提供的配置
                List<ProxyNode> proxies = providers
                   .Where(entry => "http".Equals(entry.Value["type"]) && entry.Value["url"]?.StartsWith("http"))
                   .Select((entry) => (List<ProxyNode>)GetConfigProxies(entry.Value["url"], includeProxies, includeProviders))
                   .SelectMany(list => list).ToList();
                // 添加到节点列表
                proxyList.AddRange(proxies);
            }
            return proxyList;
        }
        catch (Exception ex)
        {
            Logger.Warn("解析配置" + config + "文件出错：" + ex.Message);
        }
        return proxyList;
    }

    public class MetaInfo(string config, string configPath, PortManager portManager, List<ProxyNode> proxies)
    {
        public string Config { get; set; } = config;
        public string ConfigPath { get; set; } = configPath;
        public PortManager PortManager { get; set; } = portManager;
        public List<ProxyNode> Proxies { get; set; } = proxies;
    }

    public static string GetConfigTemplate(string resourceName) => string.Join(Environment.NewLine, [Resources.ReadAsText("template.common.yaml"), Resources.ReadAsText(resourceName)]);

    public static MetaInfo GenerateMixedConfig(List<ProxyNode> proxies)
    {
        // 读取模板内容
        string yaml = GetConfigTemplate("template.mixed.yaml");
        // mixed移除监听端口,防止多线程情况下端口冲突
        List<Regex> regexes = ((List<string>)["port", "socks-port", "mixed-port", "redir-port", "tproxy-port", "external-controller"])
            .Select(item => new Regex(@$"^{item} *?: *.+$", RegexOptions.Compiled)).ToList();
        yaml = string.Join(Environment.NewLine, yaml.Split(Environment.NewLine).Where(line => !regexes.Where(regex => regex.IsMatch(line.Trim())).Any()));
        // 关闭GEO自动更新，防止更新异常终止，导致后续不能处理IP
        yaml = yaml.Replace("geo-auto-update: true", "geo-auto-update: false");

        PortManager portManager = PortManager.Claim(proxies.Count);
        // mixed监听端口
        string listenerList = string.Join(Environment.NewLine, proxies.Select((proxy, index) => $"- name: mixed{portManager.Get(index)}{Environment.NewLine}  type: mixed{Environment.NewLine}  port: {portManager.Get(index)}{Environment.NewLine}  proxy: {Json.SerializeObject(proxy.Name)}"));
        // mixed出口代理
        string proxyList = string.Join(Environment.NewLine, proxies.Select((proxy, index) => $"  - {Json.SerializeObject(proxy.Info)}"));

        // 生成配置文件
        string config = yaml
            .Replace("listeners: []", $"listeners: {Environment.NewLine}{listenerList}")
            .Replace("proxies: []", $"proxies: {Environment.NewLine}{proxyList}");

        // 处理参数
        config = MetaPostProperty.Resolve(config);

        // 输出到文件
        string configPath = Path.Combine(Constants.WorkSpaceTemp, "mixed", Guid.NewGuid().ToString() + ".yaml");
        Files.WriteToFile(new MemoryStream(Encoding.UTF8.GetBytes(config)), configPath);

        // 节点配置本地代理
        proxies = proxies.Select((proxy, index) =>
        {
            proxy.Mixed = new WebProxy("127.0.0.1", portManager.Get(index));
            return proxy;
        }).ToList();

        // 返回服务信息
        return new(config, configPath, portManager, proxies);
    }

    public static string GenerateConfig(List<ProxyNode> proxies)
    {
        return Context.Options.GroupType switch
        {
            GroupType.standard => GenerateStandardConfig(proxies),
            GroupType.regieon => GenerateRegionConfig(proxies),
            _ => string.Empty,
        };
    }

    private static string GenerateStandardConfig(List<ProxyNode> proxies)
    {
        CommandLineOptions options = Context.Options;
        // 读取模板内容
        string yaml = GetConfigTemplate("template.standard.yaml");

        // 代理列表
        string proxyList = string.Join(Environment.NewLine, proxies.Select((proxy, index) => $"  - {Json.SerializeObject(proxy.Info)}"));

        // 读取规则集
        string rules = MetaRule.GetRuleSetRules(options.RuleSet);

        // 生成配置文件
        string config = yaml
            .Replace("proxies: []", $"proxies: {Environment.NewLine}{proxyList}")
            .Replace("rules: []", $"{rules}");

        // 处理参数
        config = MetaPostProperty.Resolve(config);

        return config;
    }

    private static string GenerateRegionConfig(List<ProxyNode> proxies)
    {
        CommandLineOptions options = Context.Options;
        // 读取模板内容
        string yaml = GetConfigTemplate("template.region.yaml");

        // 代理列表
        string proxyList = string.Join(Environment.NewLine, proxies.Select((proxy, index) => $"  - {Json.SerializeObject(proxy.Info)}"));

        // 特殊分组处理
        proxies.ForEach(proxy =>
        {
            // Cloudflare节点分组
            if (proxy.GeoInfo.Organization.Contains("Cloudflare", StringComparison.CurrentCultureIgnoreCase))
            {
                proxy.GeoInfo.CountryCode = "Cloudflare";
                proxy.GeoInfo.Country = "Cloudflare";
            }
        });

        // 代理组排序(默认按国家代码升序)
        List<string> groupOrder = proxies.Select(proxy => proxy.GeoInfo.CountryCode).Order().Distinct().ToList();
        // 按照分组内节点平均延迟升序
        if (SortPreference.delay.Equals(options.SortPreference) && (options.DelayTestEnable ?? true))
        {
            groupOrder = proxies
                .GroupBy(proxy => proxy.GeoInfo.CountryCode)
                .OrderBy(group => group.Select(proxy => proxy.DelayResult.Result()).Where(delay => delay > 0).Average())
                .Select(group => group.Key)
                .ToList();
        }
        // 按照分组内节点平均下载速度降序
        if (SortPreference.speed.Equals(options.SortPreference) && (options.SpeedTestEnable ?? true))
        {
            groupOrder = proxies
                .GroupBy(proxy => proxy.GeoInfo.CountryCode)
                .OrderByDescending(group => group.Select(proxy => proxy.SpeedResult.Result()).Where(speed => speed > 0).Average())
                .Select(group => group.Key)
                .ToList();
        }

        // 代理组列表
        List<string> groupNames = [];
        string groupList = string.Join(Environment.NewLine, proxies
            .GroupBy(proxy => proxy.GeoInfo.Country)
            .OrderBy(group => groupOrder.IndexOf(group.ToList()[0].GeoInfo.CountryCode))
            .Select(group =>
            {
                string country = group.ToList()[0].GeoInfo.Country + "节点";
                string icon = group.ToList()[0].GeoInfo.Icon;
                groupNames.Add(country);
                return
                  "  - name: " + country + Environment.NewLine
                + "    type: url-test" + Environment.NewLine
                + "    tolerance: 50" + Environment.NewLine
                + "    lazy: false" + Environment.NewLine
                + "    interval: 300" + Environment.NewLine
                + "    timeout: 2000" + Environment.NewLine
                + "    url: ${options.DelayTestUrl}" + Environment.NewLine
                + "    max-failed-times: 3" + Environment.NewLine
                + "    icon: ${" + icon + "}" + Environment.NewLine
                + "    hidden: false" + Environment.NewLine
                + "    proxies: [" + string.Join(", ", group.Select(proxy => "'" + proxy.Name + "'")) + "]" + Environment.NewLine;
            }).ToList()
        );

        // 读取规则集
        string rules = MetaRule.GetRuleSetRules(options.RuleSet);

        // 生成配置文件
        string config = yaml
            .Replace("proxies: []", $"proxies: {Environment.NewLine}{proxyList}")
            .Replace("# proxy-groups:", groupList)
            .Replace("\"${region-groups}\"", string.Join(", ", groupNames.Distinct().Select(name => "'" + name + "'")))
            .Replace("rules: []", $"{rules}");

        // 处理参数
        config = MetaPostProperty.Resolve(config);

        return config;
    }
}