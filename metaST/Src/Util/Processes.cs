using System.Diagnostics;
using System.Text;

namespace Util;

public class Processes
{
    public static Task<Process> Start(string path, string args, DataReceivedEventHandler? handler = null, bool redirectOutput = true, bool redirectError = true)
    {
        Process process;
        Task<Process> task = Task.Run(() =>
        {
            process = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = path,
                    Arguments = args,
                    RedirectStandardOutput = redirectOutput,
                    RedirectStandardError = redirectError,
                    StandardOutputEncoding = Encoding.UTF8,
                    StandardErrorEncoding = Encoding.UTF8,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                }
            };
            process.OutputDataReceived += handler ?? ((sender, e) => Console.WriteLine(e.Data));
            process.ErrorDataReceived += handler ?? ((sender, e) => Console.WriteLine(e.Data));
            process.Start();
            process.BeginOutputReadLine();
            return process;
        });
        return task;
    }

    public static void FindAndKill(string processName)
    {
        Process[] processes = Process.GetProcessesByName(Path.GetFileNameWithoutExtension(processName));
        try
        {
            foreach (var process in processes)
            {
                process?.Kill();
            }
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Error killing process {processName} : {ex.Message}");
        }
    }

    public static void Kill(Process? process)
    {
        if (process != null)
        {
            using (process)
            {
                try
                {
                    process.Kill();
                }
                catch { }
            }
        }
    }
}
