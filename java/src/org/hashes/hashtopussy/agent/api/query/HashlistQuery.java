package org.hashes.hashtopussy.agent.api.query;

public enum HashlistQuery {
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
  HASHLIST {
    @Override
    public String identifier() {
      return "hashlist";
    }
  };
  
  public abstract String identifier();
}
