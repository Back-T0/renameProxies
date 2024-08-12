using System.Net;

namespace Core.Test;
public abstract class Profiler<T>
{
    public abstract Task<T> TestAsync(IWebProxy? proxy);
}