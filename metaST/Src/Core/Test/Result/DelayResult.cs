using Util;

namespace Core.Test.Reuslt;

public class DelayResult : TestResult
{
    public List<double> delays = [];

    public override bool IsSuccess() => delays.Any(delay => delay > 0);

    public override double Result() => IsSuccess() ? delays.Average() : -1;

    // 打印颜色和阈值
    private static readonly ConsoleColor[] colors = [ConsoleColor.DarkGreen, ConsoleColor.Green, ConsoleColor.Yellow, ConsoleColor.DarkYellow, ConsoleColor.Red, ConsoleColor.DarkRed];
    private static readonly int[] thresholds = [500, 800, 1500, 3000, 5000, int.MaxValue];
    public override void Print(string prefix)
    {
        bool flag = IsSuccess();
        double delay = Result();
        string format = flag ? "{0} {1}ms" : "{0} {1}";
        string message = flag ? string.Format(format, prefix, Convert.ToInt32(delay)) : string.Format(format, prefix, ErrMsg);
        ConsoleColor color = flag ? colors[thresholds.Order().Where((threshold, index) => delay < threshold).Select((threshold, index) => index).First()] : ConsoleColor.DarkRed;
        Logger.Log(LogLevel.info, message, color);
    }
}