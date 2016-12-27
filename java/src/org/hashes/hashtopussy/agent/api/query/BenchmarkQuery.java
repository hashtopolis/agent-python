package org.hashes.hashtopussy.agent.api.query;

public enum BenchmarkQuery {
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
  },
  PROGRESS {
    @Override
    public String identifier() {
      return "progress";
    }
  },
  TOTAL {
    @Override
    public String identifier() {
      return "total";
    }
  },
  STATE {
    @Override
    public String identifier() {
      return "state";
    }
  };
  
  public abstract String identifier();
}
