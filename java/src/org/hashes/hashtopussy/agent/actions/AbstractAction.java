package org.hashes.hashtopussy.agent.actions;

/**
 * Created by sein on 15.12.16.
 */
public abstract class AbstractAction implements Action {
  protected ActionType actionType;
  
  public ActionType getType() {
    return this.actionType;
  }
}
