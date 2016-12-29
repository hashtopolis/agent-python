package org.hashes.hashtopussy.agent.common;

import org.hashes.hashtopussy.agent.objects.Benchmark;
import org.hashes.hashtopussy.agent.objects.Chunk;
import org.hashes.hashtopussy.agent.objects.Task;

public class ClientStatus {
  private boolean isLoggedin = false;
  private Benchmark benchmark = null;
  private Task task = null;
  private Chunk chunk = null;
  private ClientState clientState = ClientState.INIT;
  
  public void setIsLoggedin(boolean isLoggedin) {
    this.isLoggedin = isLoggedin;
  }
  
  public boolean getIsLoggedin() {
    return isLoggedin;
  }
  
  public Chunk getChunk() {
    return chunk;
  }
  
  public void setChunk(Chunk chunk) {
    this.chunk = chunk;
  }
  
  public Task getTask() {
    return task;
  }
  
  public void setTask(Task task) {
    this.task = task;
  }
  
  public Benchmark getBenchmark() {
    return benchmark;
  }
  
  public void setBenchmark(Benchmark benchmark) {
    this.benchmark = benchmark;
  }
  
  public ClientState getCurrentState() {
    return clientState;
  }
  
  public void setCurrentState(ClientState state) {
    if (clientState == ClientState.ERROR) {
      return; //If an error state happened, this cannot be changed anymore
    }
    clientState = state;
  }
  
  public void reset(){
    clientState = ClientState.LOGIN_DONE;
    chunk = null;
    task = null;
    benchmark = null;
  }
}
