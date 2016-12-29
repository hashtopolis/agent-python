package org.hashes.hashtopussy.agent.actions;

import org.hashes.hashtopussy.agent.api.Request;
import org.hashes.hashtopussy.agent.api.query.BenchmarkQuery;
import org.hashes.hashtopussy.agent.api.query.KeyspaceQuery;
import org.hashes.hashtopussy.agent.api.response.BenchmarkResponse;
import org.hashes.hashtopussy.agent.api.response.ErrorResponse;
import org.hashes.hashtopussy.agent.api.response.KeyspaceResponse;
import org.hashes.hashtopussy.agent.common.*;
import org.hashes.hashtopussy.agent.exceptions.InvalidQueryException;
import org.hashes.hashtopussy.agent.exceptions.InvalidUrlException;
import org.hashes.hashtopussy.agent.exceptions.WrongResponseCodeException;
import org.hashes.hashtopussy.agent.objects.Benchmark;
import org.json.JSONObject;

import java.io.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

public class BenchmarkAction extends AbstractAction {
  
  public BenchmarkAction() {
    this.actionType = ActionType.BENCHMARK;
  }
  
  @Override
  public JSONObject act(Map<MappingType, Object> mapping) throws WrongResponseCodeException, InvalidQueryException, InvalidUrlException, IOException {
    ClientStatus clientStatus = ((ClientStatus) mapping.get(MappingType.CLIENTSTATUS));
  
    // build command line
    List<String> cmd = new ArrayList<>();
    cmd.add((String) Settings.get(Setting.HASHCAT_BINARY));
    cmd.add("--machine-readable");
    //TODO: handle benchmarking type
    List<String> arguments = Utils.splitArguments(clientStatus.getTask().getAttackCmd() + " " + clientStatus.getTask().getCmdPars());
    for(String a: arguments){
      if(a.equals("#HL#")){
        cmd.add("hashlists/" + clientStatus.getTask().getHashlistId());
      }
      else if(Arrays.asList(clientStatus.getTask().getFiles()).contains(a)){
        cmd.add("files/" + a);
      }
      else{
        cmd.add(a);
      }
    }
    
    // run hashcat command
    ProcessBuilder processBuilder = new ProcessBuilder();
    processBuilder.command(cmd);
    Process process = processBuilder.start();
    OutputStream os = process.getOutputStream();
    InputStream is = process.getInputStream();
    InputStreamReader isr = new InputStreamReader(is);
    BufferedReader br = new BufferedReader(isr);
    String line;
    long startTime = System.currentTimeMillis();
    while (System.currentTimeMillis() - startTime < 10000) {
      try {
        Thread.sleep(100);
      } catch (InterruptedException e) {
        // nothing
      }
    }
    if(process.isAlive()) {
      LoggerFactory.getLogger().log(LogLevel.DEBUG, "Sending q to benchmark task..");
      os.write('q');
      os.flush();
    }
    String statusLine = "";
    while((line = br.readLine()) != null) {
      if(line.contains("STATUS")){
        statusLine = line.substring(line.indexOf("STATUS"));
      }
    }
    if(statusLine.length() == 0){
      LoggerFactory.getLogger().log(LogLevel.WARN, "Benchmark was not able to get status info, you might need to increase benchmark time!");
      return new JSONObject();
    }
    
    String[] stat = statusLine.split("\t");
    long totalProgress = Long.parseLong(stat[11]);
    long benchProgress = Long.parseLong(stat[10]);
    double bench = Math.round(benchProgress/(double)totalProgress*10000000000.d)/10000000.d;
    
    // send keyspace to server
    JSONObject query = new JSONObject();
    query.put(BenchmarkQuery.ACTION.identifier(), this.actionType.getString());
    query.put(BenchmarkQuery.TOKEN.identifier(), Settings.get(Setting.TOKEN));
    query.put(BenchmarkQuery.TASK.identifier(), clientStatus.getTask().getTaskId());
    //TODO: set benchmarking type
    query.put(BenchmarkQuery.BENCHTYPE.identifier(), "old");
    //TODO: the formatting of the double value might be a bit hacky here
    query.put(BenchmarkQuery.RESULT.identifier(), String.format("%.20f", bench).replaceAll("(\\.\\d+?)0*$", "$1"));
    Request request = new Request();
    request.setQuery(query);
    JSONObject answer = request.execute();
    if (answer.get(KeyspaceResponse.RESPONSE.identifier()) == null) {
      LoggerFactory.getLogger().log(LogLevel.FATAL, "Got invalid message from server!");
      LoggerFactory.getLogger().log(LogLevel.DEBUG, answer.toString());
    } else if (!answer.get(BenchmarkResponse.RESPONSE.identifier()).equals("SUCCESS")) {
      LoggerFactory.getLogger().log(LogLevel.ERROR, "Setting benchmark result failed: " + answer.get(ErrorResponse.MESSAGE.identifier()));
      return new JSONObject();
    }
    
    if(!answer.get(BenchmarkResponse.BENCHMARK.identifier()).equals("OK")){
      LoggerFactory.getLogger().log(LogLevel.ERROR, "Server didn't accept benchmark result!");
      clientStatus.setCurrentState(ClientState.BENCHMARK_REQUIRED);
    }
    else{
      LoggerFactory.getLogger().log(LogLevel.INFO, "Server accepted benchmark result!");
      clientStatus.setCurrentState(ClientState.TASK_RECEIVED);
    }
    
    return answer;
  }
}
