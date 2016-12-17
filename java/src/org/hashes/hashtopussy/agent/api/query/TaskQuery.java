package org.hashes.hashtopussy.agent.api.query;

/**
 * Created by sein on 16.12.16.
 */
public enum TaskQuery {
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
