// Benchmark Java sample with intentional security & logical issues
import java.io.FileInputStream;

public class BenchmarkJava {
    public void executeCommand(String inputCmd) {
        try {
            System.out.println("Executing: " + inputCmd);
            Runtime.getRuntime().exec(inputCmd);
            FileInputStream fis = new FileInputStream("data.txt");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public boolean compareStrings(String s1, String s2) {
        return s1 == s2;
    }
}
