using System.Collections.Concurrent;
using System.Net;
using System.Net.Sockets;

namespace Util;

public class PortManager : IDisposable
{
    private readonly ConcurrentBag<TcpListener> listeners = [];
    private readonly ConcurrentBag<int> ports = [];
    private PortManager() { }
    public static PortManager Claim(int portNum)
    {
        PortManager manager = new();
        Parallel.For(0, portNum, (i) =>
        {
            TcpListener listener = new(IPAddress.Loopback, 0);
            listener.Start();
            manager.listeners.Add(listener);
            manager.ports.Add(((IPEndPoint)listener.LocalEndpoint).Port);
        });
        return manager;
    }

    public int Get(int index)
    {
        return ports.ElementAt(index);
    }

    public int Use(int index)
    {
        Release(listeners.ElementAt(index));
        return ports.ElementAt(index);
    }

    public void Dispose()
    {
        Task.WaitAll(listeners.Select(listener => Task.Run(() => Release(listener))).ToArray());
        GC.SuppressFinalize(this);
    }

    private static void Release(TcpListener listener)
    {
        if (listener != null)
        {
            using (listener)
            {
                int port = ((IPEndPoint)listener.LocalEndpoint).Port;
                listener.Stop();
                WaitForPortRelease(port);
            }
        }
    }

    private static void WaitForPortRelease(int port, int timeout = 5000)
    {
        using CancellationTokenSource cts = new(timeout);
        CancellationToken token = cts.Token;
        while (!token.IsCancellationRequested)
        {
            using Socket socket = new(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
            if (Task.WaitAny(socket.ConnectAsync(IPAddress.Loopback, port), Task.Delay(50)) == 0)
            {
                Thread.Sleep(50);
            }
            else
            {
                return;
            }
        }
    }
}