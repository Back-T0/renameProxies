using System.Text.RegularExpressions;
using Core.CommandLine;
using Core.CommandLine.Enum;
using Newtonsoft.Json;
using Util;

namespace Core.Meta.Config;

public partial class MetaPostProperty
{
    public static string Resolve(string config)
    {
        // 读取所有${}占位符
        Regex regex = PlaceholderRegex();
        MatchCollection matchCollection = regex.Matches(config);
        List<GroupCollection> groupCollections = matchCollection.Select(match => match.Groups).DistinctBy(groups => groups[0].Value).ToList();
        // 生成替换映射
        Dictionary<string, string> replacements = groupCollections.ToDictionary(groups => groups[0].Value, groups => ResolveProrpertyValue(groups[1].Value));
        // 替换掉占位符
        foreach (KeyValuePair<string, string> entry in replacements)
        {
            config = config.Replace(entry.Key, entry.Value);
        }
        return config;
    }

    private static string ResolveProrpertyValue(string prorperty)
    {
        // 处理命令行参数
        if (prorperty.StartsWith("options")) return ResolveOptionValue(prorperty);
        // 处理图标资源
        if (prorperty.StartsWith("icons")) return ResolveIcon(prorperty);
        throw new InvalidDataException($"处理配置属性值错误，未知的属性: {prorperty}");
    }

    private static string ResolveOptionValue(string prorperty)
    {
        CommandLineOptions options = Context.Options;
        string json = JsonConvert.SerializeObject(options);
        Dictionary<string, dynamic>? optionMap = JsonConvert.DeserializeObject<Dictionary<string, object>>(json);
        prorperty = prorperty.Replace("options.", string.Empty);
        if (optionMap != null && optionMap.TryGetValue(prorperty, out var value))
        {
            return value.ToString();
        }
        return string.Empty;
    }

    private static string ResolveIcon(string prorperty)
    {
        CommandLineOptions options = Context.Options;
        // http远程Icon
        if (options.IconType.Equals(IconType.http))
        {
            string githubMirror = options.GithubMirror;
            string repository = "https://fastly.jsdelivr.net/gh/dongchengjie/metaST@main/metaST/Resources/";
            string extension = Path.GetExtension(prorperty);
            string iconPath = prorperty.Replace(".", "/").Replace(extension.Replace(".", "/"), extension);
            return $"{repository}{iconPath}";
        }
        // Base64编码Icon
        byte[] bytes = Resources.ReadAsBytes(prorperty);
        bytes = bytes.Length > 0 ? bytes : Resources.ReadAsBytes(prorperty = "icons.unknown.svg");
        string base64 = Convert.ToBase64String(bytes);
        if (prorperty.EndsWith(".jpeg") || prorperty.EndsWith(".jpg"))
        {
            return "data:image/jpeg;base64," + base64;
        }
        if (prorperty.EndsWith(".svg"))
        {
            return "data:image/svg+xml;base64," + base64;
        }
        return "data:image/png;base64," + base64;
    }

    [GeneratedRegex(@"\$\{(.*?)\}")]
    private static partial Regex PlaceholderRegex();
}