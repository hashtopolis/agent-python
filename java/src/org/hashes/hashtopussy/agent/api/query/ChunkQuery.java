package org.hashes.hashtopussy.agent.api.query;

public enum ChunkQuery {
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
      return "taskId";
    }
  };
  
  public abstract String identifier();
}
