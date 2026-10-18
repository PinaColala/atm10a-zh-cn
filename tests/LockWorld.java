// SPDX-License-Identifier: GPL-3.0-or-later
import java.nio.channels.FileChannel;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
public class LockWorld {
    public static void main(String[] args) throws Exception {
        try (var channel = FileChannel.open(Path.of(args[0]), StandardOpenOption.READ, StandardOpenOption.WRITE);
             var lock = channel.lock()) {
            System.out.println("LOCKED");
            System.out.flush();
            System.in.read();
        }
    }
}
