using System.Collections.Concurrent;
using System.Diagnostics;
using System.Text;
using Timer = System.Timers.Timer;

namespace Util;
public class Logger
{
    // 默认日志级别
    public static LogLevel LogLevel { get; set; } = LogLevel.info;
    // 日志刷新间隔
    public static double RefreshInterval { get; set; } = 1000;
    // 日志输出文件
    public static string LogPath { get; set; } = AppDomain.CurrentDomain.BaseDirectory;
    private static readonly string logFileName = DateTimeOffset.Now.ToUnixTimeSeconds() + ".log";
    // 前置处理器
    public static Func<string, bool, string> PreProcessor { get; set; } = (str, console) => str;
    // 控制台原始颜色
    public static readonly ConsoleColor primitiveColor = Console.ForegroundColor;
    protected static readonly Timer timer;
    // 日志队列
    protected static readonly ConcurrentQueue<Log> queue = new();
    static Logger()
    {
        // 设置控制台编码
        Console.OutputEncoding = Encoding.UTF8;
        // 启动定时器
        timer = new Timer { Interval = RefreshInterval };
        timer.Elapsed += (sender, e) => Flush();
        timer.Start();
    }

    public static void Terminate()
    {
        timer.Stop();
        Flush();
    }

    private static void Flush()
    {
        lock (queue)
        {
            List<Log> logs = [];
            while (queue.TryDequeue(out var log))
            {
                logs.Add(log);
            }
            PrintAndWrite(logs);
        }
    }
    private static void PrintAndWrite(IEnumerable<Log> logs)
    {
        // 打印到控制台
        string lines = string.Empty;
        foreach (Log log in logs)
        {
            Console.ForegroundColor = log.Color;
            Console.WriteLine(PreProcessor(log.ToString(), true));
            lines = lines + PreProcessor(log.ToString(), false) + Environment.NewLine;
        }
        // 恢复颜色
        Console.ForegroundColor = primitiveColor;
        // 写入文件
        using MemoryStream stream = new(Encoding.UTF8.GetBytes(lines));
        Directory.CreateDirectory(Path.Combine(LogPath, "log"));
        string logFile = Path.Combine(LogPath, "log", logFileName);
        using FileStream fileStream = new(logFile, FileMode.Append);
        stream.CopyTo(fileStream);
    }

    public static void Log(LogLevel level, object message, ConsoleColor color)
    {
        if (level >= LogLevel)
        {
            Log log = new(level, message, color);
            queue.Enqueue(log);
            // trace级别直接输出
            if (LogLevel == LogLevel.trace)
            {
                Flush();
            }
        }
    }

    public static void Trace(object msg) => Log(LogLevel.trace, msg, ConsoleColor.Gray);
    public static void Debug(object msg) => Log(LogLevel.debug, msg, ConsoleColor.Blue);
    public static void Info(object msg) => Log(LogLevel.info, msg, ConsoleColor.Green);
    public static void Warn(object msg) => Log(LogLevel.warn, msg, ConsoleColor.DarkYellow);
    public static void Error(object msg) => Log(LogLevel.error, msg, ConsoleColor.Red);
    public static void Fatal(object msg) => Log(LogLevel.fatal, msg, ConsoleColor.DarkRed);
}

public enum LogLevel
{
    trace = 1,
    debug = 2,
    info = 4,
    warn = 6,
    error = 8,
    fatal = 16
}

public class Log
{
    public LogLevel Level { get; set; }
    public object Message { get; set; }
    public ConsoleColor Color { get; set; }
    public DateTime DateTime { get; set; }
    public StackTrace StackTrace { get; set; }
    public string Location { get; set; }

    public Log(LogLevel logLevel, object message, ConsoleColor color)
    {
        Level = logLevel;
        Message = message;
        Color = color;
        StackTrace = new StackTrace(true);
        StackFrame? stackFrame = StackTrace.GetFrames().Skip(3).FirstOrDefault();
        Location =
            stackFrame?.GetMethod()?.DeclaringType?.FullName
            + " # " + stackFrame?.GetMethod()
            + " at line " + stackFrame?.GetFileLineNumber() + ", col " + stackFrame?.GetFileColumnNumber();
        DateTime = DateTime.Now;
    }

    public override string ToString()
    {
        string format = Logger.LogLevel switch
        {
            LogLevel.trace => Level >= LogLevel.error ? "[{0:yyyy-MM-dd HH:mm:ss}] [{1,-5}] {2} {3} {4}" : "[{0:yyyy-MM-dd HH:mm:ss}] [{1,-5}] {2}",
            _ => "[{0:yyyy-MM-dd HH:mm:ss}] [{1,-5}] {2}",
        };
        return string.Format(format, [
            DateTime,Level,Message,Location,
            Environment.NewLine+"StackTrace: "+Environment.NewLine+"  "  + string.Join("  ", StackTrace.GetFrames().Select((f) => f.ToString()))
        ]);
    }
}