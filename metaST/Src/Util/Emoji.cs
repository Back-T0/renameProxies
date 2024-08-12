namespace Util;
public class Emoji
{
    public static string EmojiToShort(string str) => EmojiOne.EmojiOne.ToShort(str).Replace("\uFE0F", string.Empty);
}