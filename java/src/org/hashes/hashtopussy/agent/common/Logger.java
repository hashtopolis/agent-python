package org.hashes.hashtopussy.agent.common;

import java.io.PrintWriter;

/**
 * Created by sein on 15.12.16.
 */
public class Logger {
    private PrintWriter writer;
    private LogLevel level;

    public Logger(PrintWriter printWriter, LogLevel level) {
        this.writer = printWriter;
        this.level = level;
    }

    public void setLevel(LogLevel level){
        if(level == null){
            return;
        }
        this.level = level;
    }

    public void log(LogLevel level, String message) {
        if (this.level.ordinal() > level.ordinal()) {
            return;
        }
        writer.println("[TIME][" + level + "]: " + message);
        writer.flush();
    }
}
