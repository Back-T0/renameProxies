namespace Util;

public class Files
{
    public static void WriteToFile(Stream stream, string dest, bool append = false)
    {
        if (stream != null)
        {
            using (stream)
            {
                string? directory = Path.GetDirectoryName(dest);
                if (directory != null)
                {
                    Directory.CreateDirectory(directory);
                    FileMode fileMode = append ? FileMode.Append : FileMode.Create;
                    using FileStream fileStream = new(dest, fileMode);
                    stream.CopyTo(fileStream);
                }
            }
        }
    }

    public static void DeleteFile(string path)
    {
        if (File.Exists(path)) File.Delete(path);
    }

    public static void DeleteDirectory(string path, bool recursive)
    {
        if (Directory.Exists(path)) Directory.Delete(path, recursive);
    }
}

