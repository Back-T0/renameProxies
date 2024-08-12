using Newtonsoft.Json;

namespace Util;

public class Json
{
    private static readonly JsonSerializerSettings serializeSettings = new()
    {
        ReferenceLoopHandling = ReferenceLoopHandling.Ignore,   // 忽略循环引用
        NullValueHandling = NullValueHandling.Include,          // 保留null值
        StringEscapeHandling = StringEscapeHandling.Default     // 不转义
    };

    public static string SerializeObject(object obj)
    {
        return JsonConvert
            .SerializeObject(obj, serializeSettings)
            .Replace(":\"true\"", ":true")
            .Replace(":\"false\"", ":false");
    }
}