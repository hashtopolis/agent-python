package org.hashes.hashtopussy.agent.objects;

public class Task {
  private int taskId;
  private int wait;
  private String attackCmd;
  private String cmdPars;
  private int hashlistId;
  private String bench;
  private int statustimer;
  private int[] files;
  
  public Task(int taskId, int wait, String attackCmd, String cmdPars, int hashlistId, String bench, int statustimer, int[] files) {
    this.taskId = taskId;
    this.wait = wait;
    this.attackCmd = attackCmd;
    this.cmdPars = cmdPars;
    this.hashlistId = hashlistId;
    this.bench = bench;
    this.statustimer = statustimer;
    this.files = files;
  }
  
  public int getTaskId() {
    return taskId;
  }
  
  public int getWait() {
    return wait;
  }
  
  public String getAttackCmd() {
    return attackCmd;
  }
  
  public String getCmdPars() {
    return cmdPars;
  }
  
  public int getHashlistId() {
    return hashlistId;
  }
  
  public String getBench() {
    return bench;
  }
  
  public int getStatustimer() {
    return statustimer;
  }
  
  public int[] getFiles() {
    return files;
  }
}
