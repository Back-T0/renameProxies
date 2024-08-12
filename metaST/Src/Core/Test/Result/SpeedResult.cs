using Util;

namespace Core.Test.Reuslt;

public class SpeedResult : TestResult
{
    private static readonly int B = 8;
    private static readonly int KB = 1024 * B;
    private static readonly int MB = 1024 * KB;

    public List<double> bitRates = [];

    public override bool IsSuccess() => bitRates.Any(bitRate => bitRate > 0);

    public override double Result() => IsSuccess() ? bitRates.Average() : -1;

    // 打印颜色和阈值
    private static readonly ConsoleColor[] colors = [ConsoleColor.DarkGreen, ConsoleColor.Green, ConsoleColor.Yellow, ConsoleColor.DarkYellow, ConsoleColor.Red, ConsoleColor.DarkRed];
    private static readonly int[] thresholds = [8 * MB, 4 * MB, 1 * MB, 500 * KB, 100 * KB, int.MinValue];
    public override void Print(string prefix)
    {
        bool flag = IsSuccess();
        double bitRate = Result();
        string format = flag ? "{0} {1}MB/s" : "{0} {1}";
        string message = flag ? string.Format(format, prefix, (bitRate / 8 / 1024 / 1024).ToString("0.00")) : string.Format(format, prefix, ErrMsg);
        ConsoleColor color = flag ? colors[thresholds.OrderDescending().Where((threshold, index) => bitRate >= threshold).Select((threshold, index) => index).First()] : ConsoleColor.DarkRed;
        Logger.Log(LogLevel.info, message, color);
    }
}