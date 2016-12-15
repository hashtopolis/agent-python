package org.hashes.hashtopussy.agent.common;

import java.io.PrintWriter;

/**
 * Created by sein on 15.12.16.
 */
public class Settings {
    public static String getUrl() {
        return "https://alpha.hashes.org/src/api/server.php";
    }

    public static LogLevel getLogLevel() {
        return LogLevel.DEBUG;
    }

    public static PrintWriter getLogPrinter() {
        return new PrintWriter(System.out);
    }

    public static String getToken() {
        return "SPx1G7WWPp";
    }
}
