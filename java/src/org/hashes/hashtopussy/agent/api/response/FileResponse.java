package org.hashes.hashtopussy.agent.api.response;

public enum FileResponse {
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
  URL {
    @Override
    public String identifier() {
      return "url";
    }
  };
  
  public abstract String identifier();
}
