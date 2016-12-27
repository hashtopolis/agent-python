package org.hashes.hashtopussy.agent.api.query;

public enum FileQuery {
  ACTION {
    @Override
    public String identifier() {
      return "action";
    }
  },
  TOKEN {
    @Override
    public String identifier() {
      return "token";
    }
  },
  TASK {
    @Override
    public String identifier() {
      return "task";
    }
  },
  FILENAME {
    @Override
    public String identifier() {
      return "filename";
    }
  };
  
  public abstract String identifier();
}
