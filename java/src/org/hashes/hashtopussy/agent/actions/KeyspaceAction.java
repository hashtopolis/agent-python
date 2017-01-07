package org.hashes.hashtopussy.agent.actions;

import org.hashes.hashtopussy.agent.api.Request;
import org.hashes.hashtopussy.agent.api.query.ChunkQuery;
import org.hashes.hashtopussy.agent.api.query.KeyspaceQuery;
import org.hashes.hashtopussy.agent.api.response.ChunkResponse;
import org.hashes.hashtopussy.agent.api.response.ErrorResponse;
import org.hashes.hashtopussy.agent.api.response.KeyspaceResponse;
import org.hashes.hashtopussy.agent.common.*;
import org.hashes.hashtopussy.agent.exceptions.InvalidQueryException;
import org.hashes.hashtopussy.agent.exceptions.InvalidUrlException;
import org.hashes.hashtopussy.agent.exceptions.WrongResponseCodeException;
import org.hashes.hashtopussy.agent.objects.Chunk;
import org.hashes.hashtopussy.agent.objects.Task;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

public class KeyspaceAction extends AbstractAction {
  
  public KeyspaceAction() {
    this.actionType = ActionType.KEYSPACE;
  }
  
  @Override
  public JSONObject act(Map<MappingType, Object> mapping) throws WrongResponseCodeException, InvalidQueryException, InvalidUrlException, IOException {
    ClientStatus clientStatus = ((ClientStatus) mapping.get(MappingType.CLIENTSTATUS));
  
    // build command line
    List<String> cmd = new ArrayList<>();
    cmd.add((String) Settings.get(Setting.HASHCAT_BINARY));
    cmd.add("--machine-readable");
    cmd.add("--keyspace");
    List<String> arguments = Utils.splitArguments(clientStatus.getTask().getAttackCmd() + " " + clientStatus.getTask().getCmdPars());
    //TODO: I don't like this, it's very hacky. Should be done better
    for(String a: arguments){
      if(a.contains("--hash-type")){
        continue;
      }
      else if(a.equals("#HL#")){
        //ignore, as this argument shouldn't be in command line on benchmark
      }
      else if(Arrays.asList(clientStatus.getTask().getFiles()).contains(a)){
        cmd.add("files/" + a);
      }
      else{
        cmd.add(a);
      }
    }
    
    LoggerFactory.getLogger().log(LogLevel.DEBUG, "Keyspace measure: " + cmd.toString());
    
    // run hashcat command
    ProcessBuilder processBuilder = new ProcessBuilder();
    processBuilder.command(cmd);
    Process process = processBuilder.start();
    InputStream is = process.getInputStream();
    InputStream eis = process.getErrorStream();
    InputStreamReader isr = new InputStreamReader(is);
    InputStreamReader eisr = new InputStreamReader(eis);
    BufferedReader br = new BufferedReader(isr);
    BufferedReader ebr = new BufferedReader(eisr);
    String line;
    String output = "";
    while ((line = br.readLine()) != null) {
      output = line;
    }
    
    String error = "";
    while ((line = ebr.readLine()) != null) {
      error += line + "\n";
    }
    if(error.length() > 0){
      LoggerFactory.getLogger().log(LogLevel.ERROR, "Keyspace measuring error: " + error);
    }
    
    LoggerFactory.getLogger().log(LogLevel.DEBUG, "Keyspace result: " + output);
    
    // send keyspace to server
    JSONObject query = new JSONObject();
    query.put(KeyspaceQuery.ACTION.identifier(), this.actionType.getString());
    query.put(KeyspaceQuery.TOKEN.identifier(), Settings.get(Setting.TOKEN));
    query.put(KeyspaceQuery.TASK.identifier(), clientStatus.getTask().getTaskId());
    query.put(KeyspaceQuery.KEYSPACE.identifier(), Integer.parseInt(output));
    Request request = new Request();
    request.setQuery(query);
    JSONObject answer = request.execute();
    if (answer.get(KeyspaceResponse.RESPONSE.identifier()) == null) {
      LoggerFactory.getLogger().log(LogLevel.FATAL, "Got invalid message from server!");
      LoggerFactory.getLogger().log(LogLevel.DEBUG, answer.toString());
    } else if (!answer.get(KeyspaceResponse.RESPONSE.identifier()).equals("SUCCESS")) {
      LoggerFactory.getLogger().log(LogLevel.ERROR, "Getting chunk failed: " + answer.get(ErrorResponse.MESSAGE.identifier()));
      return new JSONObject();
    }
    
    if(!answer.get(KeyspaceResponse.KEYSPACE.identifier()).equals("OK")){
      LoggerFactory.getLogger().log(LogLevel.ERROR, "Server didn't accept keyspace result!");
      clientStatus.setCurrentState(ClientState.KEYSPACE_REQUIRED);
    }
    else{
      LoggerFactory.getLogger().log(LogLevel.INFO, "Server accepted keyspace result!");
      clientStatus.setCurrentState(ClientState.TASK_RECEIVED);
    }
    
    return answer;
  }
}
