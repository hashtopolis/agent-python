package org.hashes.hashtopussy.agent.api.response;

public enum ErrorResponse {
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
  MESSAGE {
    @Override
    public String identifier() {
      return "message";
    }
  };
  
  public abstract String identifier();
}
