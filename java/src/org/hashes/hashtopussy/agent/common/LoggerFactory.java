package org.hashes.hashtopussy.agent.common;

import java.io.PrintWriter;

/**
 * Created by sein on 15.12.16.
 */
public class LoggerFactory {
    private static Logger logger;

    public static Logger getLogger() {
        if (logger != null) {
            return logger;
        }
        logger = new Logger(((LoggerType) Settings.get(Setting.LOGGER)).getPrinter(), (LogLevel) Settings.get(Setting.LOG_LEVEL));
        return logger;
    }
}
