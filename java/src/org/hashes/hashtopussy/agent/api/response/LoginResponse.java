package org.hashes.hashtopussy.agent.api.response;

public enum LoginResponse {
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
  TIMEOUT {
    @Override
    public String identifier() {
      return "timeout";
    }
  };
  
  public abstract String identifier();
}
