using System.Reflection;
using System.Text;

namespace Util;

public class Resources
{
    public static void Extract(string resourceName, string dest, bool skipIfExists = false)
    {
        string resourcePath = ResourcePath(resourceName);
        // 如果文件已存在则跳过
        if (skipIfExists && File.Exists(dest)) return;
        try
        {
            string? directory = Path.GetDirectoryName(dest);
            if (directory != null)
            {
                Directory.CreateDirectory(directory);
                using Stream? stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(resourcePath);
                using FileStream fileStream = new(dest, FileMode.Create);
                stream?.CopyTo(fileStream);
            }
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine($"Error extracting resouce '{resourcePath}': {ex.Message}");
        }
    }

    public static string ReadAsText(string resourceName, Encoding? encoding = null)
    {
        string resourcePath = ResourcePath(resourceName);
        using Stream? stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(resourcePath);
        if (stream is null) return string.Empty;

        using StreamReader reader = new(stream, encoding ??= Encoding.UTF8);
        return reader.ReadToEnd();
    }

    public static byte[] ReadAsBytes(string resourceName)
    {
        string resourcePath = ResourcePath(resourceName);
        using Stream? stream = Assembly.GetExecutingAssembly().GetManifestResourceStream(resourcePath);
        if (stream is null) return [];

        using MemoryStream memoryStream = new();
        stream.CopyTo(memoryStream);
        return memoryStream.ToArray();
    }

    private static string ResourcePath(string resourceName) => Assembly.GetExecutingAssembly().GetName().Name + ".Resources." + resourceName;
}
