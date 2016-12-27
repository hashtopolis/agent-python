package org.hashes.hashtopussy.agent;

import org.hashes.hashtopussy.agent.actions.*;
import org.hashes.hashtopussy.agent.cli.CommandLineParser;
import org.hashes.hashtopussy.agent.common.*;
import org.json.JSONObject;

import java.util.HashMap;
import java.util.Map;
import java.util.Scanner;

public class Client {
  private boolean isRunning;
  private ClientStatus clientStatus;
  
  public Client() {
    clientStatus = new ClientStatus();
  }
  
  public void run() {
    try {
      LoggerFactory.getLogger().log(LogLevel.DEBUG, "Entered running loop");
      isRunning = true;
      Action action;
      JSONObject answer;
      Map<MappingType, Object> mapping;
      Scanner input = new Scanner(System.in);
      while (isRunning) {
        switch (clientStatus.getCurrentState()) {
          case INIT:
            //register agent if required
            if (Settings.get(Setting.TOKEN) != null) {
              clientStatus.setCurrentState(ClientState.LOGIN_READY);
              break;
            }
            System.out.print("Client needs to be registered, please enter a voucher: ");
            mapping = new HashMap<>();
            while (!input.hasNext()) {
              Thread.sleep(100);
            }
            mapping.put(MappingType.VOUCHER, input.nextLine());
            action = new RegisterAction();
            action.act(mapping);
            if (Settings.get(Setting.TOKEN) != null) {
              clientStatus.setCurrentState(ClientState.LOGIN_READY);
            }
            break;
          case LOGIN_READY:
            //login agent
            action = new LoginAction();
            action.act(null);
            clientStatus.setIsLoggedin(true);
            //TODO: we need to check here if new binaries are available
            clientStatus.setCurrentState(ClientState.LOGIN_DONE);
            break;
          case LOGIN_DONE:
            // get a task
            action = new TaskAction();
            mapping = new HashMap<>();
            mapping.put(MappingType.CLIENTSTATUS, clientStatus);
            action.act(mapping);
            if (clientStatus.getTask() != null) {
              // when task is received, we need to download files and hashlist
              if(Utils.downloadsRequired(clientStatus)){
                clientStatus.setCurrentState(ClientState.DOWNLOADS_REQUIRED);
                break;
              }
              Utils.printTaskInfo(clientStatus.getTask());
              clientStatus.setCurrentState(ClientState.TASK_RECEIVED);
            } else {
              Thread.sleep(5000);
            }
            break;
          case TASK_RECEIVED:
            // get a chunk
            action = new ChunkAction();
            mapping = new HashMap<>();
            mapping.put(MappingType.CLIENTSTATUS, clientStatus);
            action.act(mapping);
            if (clientStatus.getChunk() != null) {
              Utils.printChunkInfo(clientStatus.getChunk());
              clientStatus.setCurrentState(ClientState.CHUNK_RECEIVED);
            } else if (clientStatus.getCurrentState() != ClientState.BENCHMARK_REQUIRED && clientStatus.getCurrentState() != ClientState.KEYSPACE_REQUIRED) {
              Thread.sleep(5000);
            }
            break;
          case BENCHMARK_REQUIRED:
            // do the benchmark
            action = new BenchmarkAction();
            mapping = new HashMap<>();
            mapping.put(MappingType.CLIENTSTATUS, clientStatus);
            action.act(mapping);
            break;
          case KEYSPACE_REQUIRED:
            // do keyspace calculation
            action = new KeyspaceAction();
            mapping = new HashMap<>();
            mapping.put(MappingType.CLIENTSTATUS, clientStatus);
            action.act(mapping);
            if (clientStatus.getCurrentState() != ClientState.TASK_RECEIVED) {
              Thread.sleep(5000);
            }
            break;
          case CHUNK_RECEIVED:
            // do cracking process
            //TODO: do cracking
            break;
          case DOWNLOADS_REQUIRED:
            // download file dependencies
            action = new DownloadAction();
            mapping = new HashMap<>();
            mapping.put(MappingType.CLIENTSTATUS, clientStatus);
            action.act(mapping);
            if(!Utils.downloadsRequired(clientStatus)){
              clientStatus.setCurrentState(ClientState.TASK_RECEIVED);
            }
            else{
              LoggerFactory.getLogger().log(LogLevel.WARN, "Retry downloading files in 5 seconds...");
              Thread.sleep(5000);
            }
            break;
          case ERROR:
            LoggerFactory.getLogger().log(LogLevel.FATAL, "Client is in ERROR state, aborting!");
            System.exit(-1);
        }
        Thread.sleep(100);
      }
      LoggerFactory.getLogger().log(LogLevel.NORMAL, "HTP Client loop finished");
      input.close();
    } catch (Exception e) {
      e.printStackTrace();
      LoggerFactory.getLogger().log(LogLevel.FATAL, e.getClass() + " -> " + e.getMessage());
    }
  }
  
  public static void main(String[] args) {
    Settings.get(Setting.URL);
    new CommandLineParser().parse(args);
    new Client().run();
  }
}
