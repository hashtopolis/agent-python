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
  BENCHTYPE {
    @Override
    public String identifier() {
      return "type";
    }
  },
  RESULT {
    @Override
    public String identifier() {
      return "result";
    }
  };
  
  public abstract String identifier();
}
