package org.hashes.hashtopussy.agent.common;

import java.io.PrintWriter;

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
