using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace Util;

public class YamlDot
{
    public static Dictionary<dynamic, dynamic> DeserializeObject(string yaml)
    {
        return new DeserializerBuilder()
            .WithNamingConvention(NullNamingConvention.Instance)
            .Build()
            .Deserialize<dynamic>(yaml);
    }
}