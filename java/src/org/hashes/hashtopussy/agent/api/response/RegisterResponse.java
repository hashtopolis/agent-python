package org.hashes.hashtopussy.agent.api.response;

public enum RegisterResponse {
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
  TOKEN {
    @Override
    public String identifier() {
      return "token";
    }
  };
  
  public abstract String identifier();
}
