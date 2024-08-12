using CommandLine;
using CommandLine.Text;
using Core.CommandLine;
using Core.MetaSpeedTest;

internal class Program
{
    // 主程序类名
    private static readonly Type application = typeof(MetaSpeedTest);

    public static void Main(string[] args)
    {
        Parser parser = new(with => with.HelpWriter = null);
        ParserResult<CommandLineOptions> result = parser.ParseArguments<CommandLineOptions>(args);
        result
            .WithParsed(options => application?.GetMethod("Main")?.Invoke(null, [options])) // 执行程序代码
            .WithNotParsed(errs => DisplayHelp(result, errs));                              // 打印帮助信息
    }

    private static void DisplayHelp<T>(ParserResult<T> result, IEnumerable<Error> errs)
    {
        if (errs.IsVersion())
        {
            Console.WriteLine(HelpText.AutoBuild(result));
        }
        else
        {
            Console.WriteLine(HelpText.AutoBuild(result, settings =>
            {
                settings.AddDashesToOption = true;              // 显示破折号
                settings.AddEnumValuesToHelpText = true;        // 描述枚举值的取值范围
                settings.AdditionalNewLineAfterOption = true;   // 描述末尾空新行
                settings.AutoHelp = true;                       // 自动生成--help
                settings.AutoVersion = true;                    // 自动生成--version
                settings.Copyright = string.Empty;              // 版权信息
                settings.Heading = string.Empty;                // 顶部信息
                settings.MaximumDisplayWidth = 128;             // 单行展示字数限制
                return HelpText.DefaultParsingErrorsHandler(result, settings);
            }, e => e));
        }
    }
}
