package org.hashes.hashtopussy.agent;

import org.hashes.hashtopussy.agent.actions.Action;
import org.hashes.hashtopussy.agent.actions.LoginAction;
import org.hashes.hashtopussy.agent.actions.MappingType;
import org.hashes.hashtopussy.agent.actions.RegisterAction;
import org.hashes.hashtopussy.agent.cli.CommandLineParser;
import org.hashes.hashtopussy.agent.common.*;
import org.json.JSONObject;

import java.util.HashMap;
import java.util.Map;
import java.util.Scanner;

/**
 * Created by sein on 03.12.16.
 */
public class Client {
  public boolean isRunning;
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
      Scanner input = new Scanner(System.in);
      while (isRunning) {
        switch (clientStatus.getCurrentState()) {
          case INIT:
            if (Settings.get(Setting.TOKEN) != null) {
              clientStatus.setCurrentState(ClientState.LOGIN_READY);
              break;
            }
            System.out.print("Client needs to be registered, please enter a voucher: ");
            Map<MappingType, Object> mapping = new HashMap<>();
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
            clientStatus.setCurrentState(ClientState.LOGIN_DONE);
            break;
          case LOGIN_DONE:
            //TODO: get a task
            break;
          case TASK_RECEIVED:
            //TODO: get a chunk
            break;
          case BENCHMARK_REQUIRED:
            //TODO: do benchmark
            clientStatus.setCurrentState(ClientState.TASK_RECEIVED);
            break;
          case KEYSPACE_REQUIRED:
            //TODO: do keyspace calc
            clientStatus.setCurrentState(ClientState.TASK_RECEIVED);
            break;
          case CHUNK_RECEIVED:
            //TODO: do cracking
            break;
          case ERROR:
            LoggerFactory.getLogger().log(LogLevel.FATAL, "Client is in ERROR state, aborting!");
            System.exit(-1);
        }
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
