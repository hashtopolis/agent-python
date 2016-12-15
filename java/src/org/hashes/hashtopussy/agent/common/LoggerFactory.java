package org.hashes.hashtopussy.agent.common;

/**
 * Created by sein on 15.12.16.
 */
public class LoggerFactory {
    private static Logger logger;

    public static Logger getLogger(){
        if( logger != null){
            return logger;
        }
        logger = new Logger(Settings.getLogPrinter(), Settings.getLogLevel());
        return logger;
    }
}
