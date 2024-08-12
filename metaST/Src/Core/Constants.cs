using System.Reflection;
using System.Runtime.InteropServices;

namespace Core;
public class Constants
{
    // 内核名称
    public static readonly string MetaCore = "mihomo";
    // 内核可执行程序名
    public static readonly string MetaExecutable = MetaCore + (RuntimeInformation.IsOSPlatform(OSPlatform.Windows) ? ".exe" : string.Empty);
    // 运行时可执行程序名(防止影响其他mihomo进程)
    public static readonly string RuntimeExecutable = Assembly.GetEntryAssembly()?.GetName().Name + "_" + MetaExecutable;
    // 用户目录
    public static readonly string UserProfile = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
    // 配置目录
    public static readonly string ConfigPath = Path.Combine(UserProfile, ".config", "mihomo");
    // 临时文件目录
    public static readonly string TempPath = Path.GetTempPath();
    // 应用程序目录
    public static readonly string AppPath = AppDomain.CurrentDomain.BaseDirectory;
    // 工作目录
    public static readonly string WorkSpace = Path.Combine(TempPath, "." + Assembly.GetEntryAssembly()?.GetName().Name);
    // 工作目录/临时目录
    public static readonly string WorkSpaceTemp = Path.Combine(WorkSpace, "temp");
    // 最大占用端口数
    public static readonly int MaxPortsOccupied = 200;
    // 最大延迟测速线程数
    public static readonly int MaxDelayTestThreads = 128;
    // 主体内容最大字符宽度
    public static readonly int MaxSubject = 64;
}