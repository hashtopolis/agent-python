package org.hashes.hashtopussy.agent.common;

import java.io.PrintWriter;

/**
 * Created by sein on 15.12.16.
 */
public enum LoggerType {
  STDOUT {
    @Override
    public PrintWriter getPrinter() {
      return new PrintWriter(System.out);
    }
  },
  FILE {
    @Override
    public PrintWriter getPrinter() {
      //TODO: add file printwriter here
      return null;
    }
  };
  
  public abstract PrintWriter getPrinter();
}
