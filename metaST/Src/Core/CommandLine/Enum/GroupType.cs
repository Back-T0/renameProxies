using System.ComponentModel;

namespace Core.CommandLine.Enum;
public enum GroupType
{
    [DefaultValue("template.standard.yaml")]
    standard,   // 标准分组

    [DefaultValue("template.region.yaml")]
    regieon     // 地域分组
}