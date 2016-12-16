package org.hashes.hashtopussy.agent.actions;

/**
 * Created by sein on 15.12.16.
 */
enum ActionType {
  REGISTER {
    public String getString() {
      return "register";
    }
  },
  LOGIN {
    public String getString() {
      return "login";
    }
  };
  //TODO: add more actionTypes
  
  public abstract String getString();
  
  public boolean isStringType(String type) {
    return type.equals(getString());
  }
}
