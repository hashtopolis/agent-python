package org.hashes.hashtopussy.agent.actions;

enum ActionType {
  REGISTER {
    @Override
    public String getString() {
      return "register";
    }
  },
  LOGIN {
    @Override
    public String getString() {
      return "login";
    }
  },
  TASK {
    @Override
    public String getString() {
      return "task";
    }
  },
  CHUNK {
    @Override
    public String getString() {
      return "chunk";
    }
  }, KEYSPACE {
    @Override
    public String getString() {
      return "keyspace";
    }
  };
  //TODO: add more actionTypes
  
  public abstract String getString();
  
  public boolean isStringType(String type) {
    return type.equals(getString());
  }
}
