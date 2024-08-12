using System.Diagnostics;
using System.Runtime.InteropServices;
using Util;

namespace Core.Meta;

public class MetaCore
{
    // 内核解压路径
    private static readonly string runtimeExecutablePath = Path.Combine(Constants.WorkSpace, Constants.RuntimeExecutable);
    static MetaCore()
    {
        // 解压内核
        string resourceName = "meta." + Platform.GetPlatform() + "." + Constants.MetaExecutable;
        Resources.Extract(resourceName, runtimeExecutablePath, true);
        // 解压GEO
        Resources.Extract("meta.country.mmdb", Path.Combine(Constants.ConfigPath, "country.mmdb"), true);
        Resources.Extract("meta.geoip.dat", Path.Combine(Constants.ConfigPath, "geoip.dat"), true);
        Resources.Extract("meta.geosite.dat", Path.Combine(Constants.ConfigPath, "geosite.dat"), true);
        // 文件赋权
        if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
        {
            Processes.Start("icacls", runtimeExecutablePath + " /grant Everyone:(RX)", (sender, e) => { });
        }
        if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
        {
            File.SetUnixFileMode(runtimeExecutablePath, UnixFileMode.OtherExecute | UnixFileMode.GroupExecute | UnixFileMode.UserExecute);
        }
    }

    public static Task<Process> StartProxy(string configPath)
    {
        TaskCompletionSource<bool> tcs = new();
        Task<Process> task = Processes.Start(runtimeExecutablePath, "-f " + configPath, (sender, e) =>
        {
            Logger.Trace(e.Data ?? string.Empty);
            if (!tcs.Task.IsCompleted && !string.IsNullOrEmpty(e.Data))
            {
                if (e.Data.Contains("Start initial Compatible provider default"))
                {
                    tcs.TrySetResult(true);
                }
                if (e.Data.Contains("level=fatal"))
                {
                    Logger.Fatal(e.Data);
                    tcs.TrySetResult(false);
                }
                if (e.Data.Contains("level=error"))
                {
                    Logger.Error(e.Data);
                }
            }
        });

        // 注册退出事件
        ExitRegistrar.RegisterAction((type) => task.Result.Kill());

        // 等待代理成功启动，超时60秒
        Logger.Debug("等待代理成功启动...");
        Task finished = Task.WhenAny(tcs.Task, Task.Delay(TimeSpan.FromSeconds(60))).Result;
        if (finished == tcs.Task)
        {
            if (!((Task<bool>)finished).Result)
            {
                task.Result.Kill();
                throw new Exception("代理启动失败");
            }
        }
        else
        {
            throw new Exception("代理启动超时");
        }
        Logger.Debug("代理启动成功");
        return task;
    }
}