package org.hashes.hashtopussy.agent.actions;

public abstract class AbstractAction implements Action {
  protected ActionType actionType;
  
  public ActionType getType() {
    return this.actionType;
  }
}
