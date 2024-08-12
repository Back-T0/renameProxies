using System.Runtime.InteropServices;

namespace Util;

public class Platform
{
    public static string GetPlatform()
    {
        string os = RuntimeInformation.IsOSPlatform(OSPlatform.Windows) ? "win" : "linux";
        string arch = RuntimeInformation.OSArchitecture.ToString();
        if ("x64".Equals(arch.ToLower()))
        {
            arch = "amd64";
        }
        else if ("arm64".Equals(arch.ToLower()))
        {
            arch = "arm64";
        }
        return $"{os}_{arch}";
    }
}