using System.Net;

namespace Util;

public class HttpRequest
{
    public static double DefaultTimeout { get; set; } = 3000;

    public static T? UsingHttpClient<T>(Func<HttpClient, T> action, double? timeout = null, IWebProxy? proxy = null)
    {
        using HttpClient client = proxy != null ?
        new HttpClient(new HttpClientHandler { Proxy = proxy, UseProxy = true }) : new HttpClient();
        client.Timeout = timeout == null ?
                   TimeSpan.FromMilliseconds(DefaultTimeout) : TimeSpan.FromMilliseconds((double)timeout);
        try
        {
            return action.Invoke(client);
        }
        catch
        {
            return default;
        }
    }

    public static string GetForBody(string url, double? timeout = null, IWebProxy? proxy = null)
    {
        return UsingHttpClient((client) =>
        {
            using HttpResponseMessage response = client.GetAsync(url).Result;
            return response.IsSuccessStatusCode ? response.Content.ReadAsStringAsync().Result : string.Empty;
        }, timeout, proxy) ?? string.Empty;
    }
}