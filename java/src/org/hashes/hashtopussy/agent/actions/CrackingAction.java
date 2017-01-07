package org.hashes.hashtopussy.agent.actions;

import org.hashes.hashtopussy.agent.api.Request;
import org.hashes.hashtopussy.agent.api.query.BenchmarkQuery;
import org.hashes.hashtopussy.agent.api.query.CrackingQuery;
import org.hashes.hashtopussy.agent.api.response.BenchmarkResponse;
import org.hashes.hashtopussy.agent.api.response.CrackingResponse;
import org.hashes.hashtopussy.agent.api.response.ErrorResponse;
import org.hashes.hashtopussy.agent.api.response.KeyspaceResponse;
import org.hashes.hashtopussy.agent.common.*;
import org.hashes.hashtopussy.agent.exceptions.InvalidQueryException;
import org.hashes.hashtopussy.agent.exceptions.InvalidUrlException;
import org.hashes.hashtopussy.agent.exceptions.WrongResponseCodeException;
import org.json.JSONArray;
import org.json.JSONObject;

import java.io.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

public class CrackingAction extends AbstractAction {
  
  public CrackingAction() {
    this.actionType = ActionType.CRACKING;
  }
  
  @Override
  public JSONObject act(Map<MappingType, Object> mapping) throws WrongResponseCodeException, InvalidQueryException, InvalidUrlException, IOException {
    ClientStatus clientStatus = ((ClientStatus) mapping.get(MappingType.CLIENTSTATUS));
  
    // build command line
    List<String> cmd = new ArrayList<>();
    cmd.add((String) Settings.get(Setting.HASHCAT_BINARY));
    cmd.add("--machine-readable");
    cmd.add("--status-timer=5");
    cmd.add("--status");
    cmd.add("--skip=" + clientStatus.getChunk().getSkip());
    cmd.add("-l=" + clientStatus.getChunk().getLength());
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
    InputStream is = process.getInputStream();
    InputStream es = process.getErrorStream();
    InputStreamReader isr = new InputStreamReader(is);
    InputStreamReader esr = new InputStreamReader(es);
    BufferedReader br = new BufferedReader(isr);
    BufferedReader ebr = new BufferedReader(esr);
    String line;
    //cracking is running
    LoggerFactory.getLogger().log(LogLevel.NORMAL, "Start cracking chunk...");
    List<String> cracks = new ArrayList<>();
    while((line = br.readLine()) != null) {
      if(line.contains(":") && !line.startsWith("Watchdog") && !line.startsWith("Hashes") && !line.startsWith("Bitmaps") && !line.startsWith("Applicable") && !line.startsWith("Pars") && !line.startsWith("Cache") && !line.startsWith("Rules")){
        cracks.add(line);
        LoggerFactory.getLogger().log(LogLevel.DEBUG, "CRACK: " + line);
      }
      if(line.contains("STATUS")){
        String statusLine = line.substring(line.indexOf("STATUS"));
        LoggerFactory.getLogger().log(LogLevel.DEBUG, statusLine);
        String[] stat = statusLine.split("\t");
        
        JSONObject query = new JSONObject();
        query.put(CrackingQuery.ACTION.identifier(), this.actionType.getString());
        query.put(CrackingQuery.TOKEN.identifier(), Settings.get(Setting.TOKEN));
        query.put(CrackingQuery.CHUNK.identifier(), clientStatus.getChunk().getChunkId());
        query.put(CrackingQuery.KPROGRESS.identifier(), Long.parseLong(stat[8]));
        query.put(CrackingQuery.PROGRESS.identifier(), Long.parseLong(stat[10]));
        query.put(CrackingQuery.SPEED.identifier(), Long.parseLong(stat[3]));
        query.put(CrackingQuery.TOTAL.identifier(), Long.parseLong(stat[11]));
        query.put(CrackingQuery.STATE.identifier(), Long.parseLong(stat[1]));
        JSONArray cracked = new JSONArray();
        for(String c: cracks){
          cracked.put(c);
        }
        query.put(CrackingQuery.CRACKS.identifier(), cracked);
        cracks.clear();
        Request request = new Request();
        request.setQuery(query);
        JSONObject answer = request.execute();
        if (answer.get(CrackingResponse.RESPONSE.identifier()) == null) {
          LoggerFactory.getLogger().log(LogLevel.FATAL, "Got invalid message from server!");
          LoggerFactory.getLogger().log(LogLevel.DEBUG, answer.toString());
        } else if (!answer.get(CrackingResponse.RESPONSE.identifier()).equals("SUCCESS")) {
          LoggerFactory.getLogger().log(LogLevel.ERROR, "Sending cracking result failed: " + answer.get(ErrorResponse.MESSAGE.identifier()));
        }
        if(!answer.isNull(CrackingResponse.ZAP.identifier())){
          //TODO: we need to handle zaps
        }
        LoggerFactory.getLogger().log(LogLevel.NORMAL, "Update sent: " + answer.get(CrackingResponse.CRACKED.identifier()) + " cracked, " + answer.get(CrackingResponse.SKIPPED.identifier()) + " skipped");
      }
    }
  
    while((line = ebr.readLine()) != null) {
      //TODO: handle error lines
      LoggerFactory.getLogger().log(LogLevel.FATAL, "Hashcat error: " + line);
    }
    
    return new JSONObject();
  }
}
