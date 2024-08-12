using System.Diagnostics;
using Core.Meta.Config;
using Util;

namespace Core.Meta;

public class MetaService
{
    public static T UsingProxies<T>(List<ProxyNode> proxies, Func<List<ProxyNode>, T> action)
    {
        // 生成mixed配置文件
        MetaConfig.MetaInfo metaInfo = MetaConfig.GenerateMixedConfig(proxies);
        Task<Process>? task = null;
        try
        {
            // 释放所有端口
            metaInfo.PortManager.Dispose();
            // 开启代理
            task = MetaCore.StartProxy(metaInfo.ConfigPath);
            // 使用代理
            return action.Invoke(metaInfo.Proxies);
        }
        finally
        {
            // 清理mixed配置文件
            Files.DeleteFile(metaInfo.ConfigPath);
            Processes.Kill(task?.Result);
        }
    }
}