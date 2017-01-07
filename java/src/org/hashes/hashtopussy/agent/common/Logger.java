package org.hashes.hashtopussy.agent.common;

import java.io.PrintWriter;
import java.text.SimpleDateFormat;
import java.util.Date;

public class Logger {
  private PrintWriter writer;
  private LogLevel level;
  
  public Logger(PrintWriter printWriter, LogLevel level) {
    this.writer = printWriter;
    this.level = level;
  }
  
  public void setLevel(LogLevel level) {
    if (level == null) {
      return;
    }
    this.level = level;
  }
  
  public void log(LogLevel level, String message) {
    if (this.level.ordinal() > level.ordinal()) {
      return;
    }
    writer.println("[" + new SimpleDateFormat("yyyy.MM.dd - HH:mm:ss.SSS").format(new Date()) + "][" + level + "]: " + message);
    writer.flush();
  }
}
