using System.Security.Cryptography;
using System.Text;

namespace Util;

public class Strings
{
    public static string Padding(string str, int width, char paddingChar = ' ', bool chinsesAsDouble = true)
    {
        if (string.IsNullOrEmpty(str))
        {
            return str;
        }
        else if (str.Length > width)
        {
            return str[..width];
        }
        int doubleCount = chinsesAsDouble ? str.Count(c => c >= '\u4E00' && c <= '\u9FFF') : 0;
        int paddingCount = width - (str.Length + doubleCount);
        return paddingCount > 0 ? str.PadRight(str.Length + paddingCount, paddingChar) : str;
    }

    public static bool IsBase64String(string base64)
    {
        if (!string.IsNullOrWhiteSpace(base64))
        {
            // padding
            base64 += Repeat("=", base64.Length % 4);
            Span<byte> buffer = new(new byte[base64.Length]);
            return Convert.TryFromBase64String(base64, buffer, out _);
        }
        return false;
    }

    public static string Base64Encoding(string str, Encoding encoding) => Convert.ToBase64String(encoding.GetBytes(str));

    public static string Base64Decoding(string base64, Encoding encoding)
    {
        // padding
        base64 += Repeat("=", base64.Length % 4);
        return encoding.GetString(Convert.FromBase64String(base64));
    }

    public static string Md5(string input)
    {
        byte[] inputBytes = Encoding.UTF8.GetBytes(input);
        byte[] hashBytes = MD5.HashData(inputBytes);
        return BitConverter.ToString(hashBytes).Replace("-", string.Empty).ToLower();
    }

    public static string Repeat(string str, int n) => string.Concat(Enumerable.Repeat(str, n));
}