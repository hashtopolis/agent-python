package org.hashes.hashtopussy.agent.actions;

/**
 * Created by sein on 15.12.16.
 */
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
  };
  //TODO: add more actionTypes
  
  public abstract String getString();
  
  public boolean isStringType(String type) {
    return type.equals(getString());
  }
}
