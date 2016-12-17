package org.hashes.hashtopussy.agent.api.query;

public enum LoginQuery {
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
  };
  
  public abstract String identifier();
}
