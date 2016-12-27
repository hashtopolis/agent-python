package org.hashes.hashtopussy.agent.actions;

abstract class AbstractAction implements Action {
  ActionType actionType;
  
  public ActionType getType() {
    return this.actionType;
  }
}
