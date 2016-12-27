package org.hashes.hashtopussy.agent.api.query;

public enum KeyspaceQuery {
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
  TASK {
    @Override
    public String identifier() {
      return "taskId";
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
