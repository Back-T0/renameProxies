using System.ComponentModel;
using System.Reflection;
using Core.CommandLine.Enum;
using Util;

namespace Core.Meta.Config;

public class MetaRule
{
    public static string GetRuleSetRules(RuleSet ruleSet)
    {
        // 读取字符集资源名称
        MemberInfo memberInfo = typeof(RuleSet).GetMember(ruleSet.ToString())[0];
        DefaultValueAttribute? defaultValue = (DefaultValueAttribute?)memberInfo.GetCustomAttribute(typeof(DefaultValueAttribute));
        string? resourceName = defaultValue?.Value?.ToString();
        if (!string.IsNullOrWhiteSpace(resourceName))
        {
            string commonRules = Resources.ReadAsText("template.ruleset.common.yaml");
            string rules = Resources.ReadAsText(resourceName);
            // 通用规则优先匹配
            return rules.Replace("rules:", commonRules);
        }
        return string.Empty;
    }
}