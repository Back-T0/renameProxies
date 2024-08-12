using System.Diagnostics;
using System.Net;
using Core.Test.Reuslt;
using Util;

namespace Core.Test.Profiler;

public class SpeedProfiler(string url = "https://speed.cloudflare.com/__down?bytes=200000000", int timeout = 3000, int duration = 10000, int rounds = 1, double failFastRatio = 0.5) : Profiler<SpeedResult>
{
    private readonly string Url = url;
    private readonly int Timeout = timeout;
    private readonly int Duration = duration;
    private readonly int Rounds = rounds;
    private readonly double FailFastRatio = failFastRatio;
    public override Task<SpeedResult> TestAsync(IWebProxy? proxy)
    {
        return Task.Run(() =>
        {
            SpeedResult result = new();
            int succeded = 0;
            for (int i = 0; i < Rounds; i++)
            {
                bool flag = HttpRequest.UsingHttpClient((client) =>
                {
                    try
                    {
                        // 快速失败: 已经测试了一定比例仍然无任何结果
                        if (succeded == 0 && i > 0 && i / FailFastRatio > Rounds) throw new TimeoutException("Speed test timeout (fail fast)");
                        Stopwatch stopwatch = Stopwatch.StartNew();
                        // 打开输入流
                        Task<Stream> task = client.GetStreamAsync(Url);
                        if (Task.WaitAny(task, Task.Delay(Timeout)) != 0) throw new TimeoutException("SpeedTest open stream timeout");
                        // 开始下载
                        byte[] buffer = new byte[1000000];
                        long len = -1;
                        double downloaded = 0;
                        using (Stream stream = task.Result)
                        {
                            while (len != 0)
                            {
                                Task<int> readTask = stream.ReadAsync(buffer, 0, buffer.Length);
                                // 读取流数据超时
                                if (Task.WaitAny(task, Task.Delay(Duration)) != 0) throw new TimeoutException("SpeedTest read timeout");
                                len = readTask.Result;
                                downloaded += len;
                                if (stopwatch.ElapsedMilliseconds > Duration)
                                {
                                    break;
                                }
                            }
                        }
                        stopwatch.Stop();
                        result.bitRates.Add(downloaded * 8 * 1000 / stopwatch.ElapsedMilliseconds);
                        return true;
                    }
                    catch (Exception ex)
                    {
                        if (typeof(AggregateException).Equals(ex.GetType()))
                        {
                            while (ex.InnerException != null) ex = ex.InnerException;
                        }
                        result.ErrMsg = ex.Message;
                        Logger.Debug($"Erroring Testing speed: {ex.Message}");
                        return false;
                    }
                }, Timeout * 2, proxy);
                succeded += flag ? 1 : 0;
            }
            return result;
        });
    }
}