package org.hashes.hashtopussy.agent.api.response;

public enum HashlistResponse {
  RESPONSE {
    @Override
    public String identifier() {
      return "response";
    }
  };
  
  public abstract String identifier();
}
