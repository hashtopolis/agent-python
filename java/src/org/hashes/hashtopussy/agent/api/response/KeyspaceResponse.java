package org.hashes.hashtopussy.agent.api.response;

public enum KeyspaceResponse {
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
  KEYSPACE {
    @Override
    public String identifier() {
      return "keyspace";
    }
  };
  
  public abstract String identifier();
}
