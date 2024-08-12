namespace Core.Test;

public abstract class TestResult
{
    public abstract bool IsSuccess();
    public string ErrMsg { get; set; } = string.Empty;
    public abstract double Result();
    public abstract void Print(string prefix);
}