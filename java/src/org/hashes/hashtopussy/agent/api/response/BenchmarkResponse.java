package org.hashes.hashtopussy.agent.api.response;

public enum BenchmarkResponse {
  ACTION {
    @Override
    public String identifier() {
      return "action";
    }
  },
  RESPONSE {
    @Override
    public String identifier() {
      return "response";
    }
  },
  BENCHMARK {
    @Override
    public String identifier() {
      return "benchmark";
    }
  };
  
  public abstract String identifier();
}
