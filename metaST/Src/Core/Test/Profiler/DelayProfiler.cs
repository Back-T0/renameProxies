using System.Diagnostics;
using System.Net;
using Core.Test.Reuslt;
using Util;

namespace Core.Test.Profiler;

public class DelayProfiler(string url = "https://www.google.com/gen_204", int timeout = 3000, int rounds = 5, double failFastRatio = 0.5) : Profiler<DelayResult>
{
    private readonly string Url = url;
    private readonly int Timeout = timeout;
    private readonly int Rounds = rounds;
    private readonly double FailFastRatio = failFastRatio;

    public override Task<DelayResult> TestAsync(IWebProxy? proxy)
    {
        return Task.Run(() =>
        {
            DelayResult result = new();
            int succeded = 0;
            for (int i = 0; i < Rounds; i++)
            {
                bool flag = HttpRequest.UsingHttpClient((client) =>
                {
                    try
                    {
                        // 快速失败: 已经测试了一定比例仍然无任何结果
                        if (succeded == 0 && i > 0 && i / FailFastRatio > Rounds) throw new TimeoutException("Delay test timeout (fail fast)");
                        // 发送HEAD请求
                        HttpRequestMessage request = new(HttpMethod.Head, Url);
                        Stopwatch stopwatch = Stopwatch.StartNew();
                        Task<HttpResponseMessage> task = client.SendAsync(request);
                        // 请求超时
                        if (Task.WaitAny(task, Task.Delay(Timeout)) != 0) throw new TimeoutException("Delay test timeout");
                        using HttpResponseMessage response = task.Result;
                        response.EnsureSuccessStatusCode();
                        stopwatch.Stop();
                        result.delays.Add(stopwatch.ElapsedMilliseconds);
                        return true;
                    }
                    catch (Exception ex)
                    {
                        if (typeof(AggregateException).Equals(ex.GetType()))
                        {
                            while (ex.InnerException != null) ex = ex.InnerException;
                        }
                        result.ErrMsg = ex.Message;
                        Logger.Debug($"Erroring Testing delay: {ex.Message}");
                        return false;
                    }
                }, Timeout * 2, proxy);
                succeded += flag ? 1 : 0;
            }
            return result;
        });
    }
}