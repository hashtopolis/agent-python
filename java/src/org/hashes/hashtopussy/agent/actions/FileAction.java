package org.hashes.hashtopussy.agent.actions;

import org.hashes.hashtopussy.agent.api.Request;
import org.hashes.hashtopussy.agent.api.query.FileQuery;
import org.hashes.hashtopussy.agent.api.response.ErrorResponse;
import org.hashes.hashtopussy.agent.api.response.FileResponse;
import org.hashes.hashtopussy.agent.common.*;
import org.hashes.hashtopussy.agent.exceptions.InvalidQueryException;
import org.hashes.hashtopussy.agent.exceptions.InvalidUrlException;
import org.hashes.hashtopussy.agent.exceptions.WrongResponseCodeException;
import org.json.JSONObject;

import java.io.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class FileAction extends AbstractAction {
  
  public FileAction() {
    this.actionType = ActionType.FILE;
  }
  
  @Override
  public JSONObject act(Map<MappingType, Object> mapping) throws WrongResponseCodeException, InvalidQueryException, InvalidUrlException, IOException {
    ClientStatus clientStatus = ((ClientStatus) mapping.get(MappingType.CLIENTSTATUS));
    
    File folder = new File("files");
    if(!folder.exists()){
      folder.mkdirs();
    }
    
    // send file request to server
    JSONObject query = new JSONObject();
    query.put(FileQuery.ACTION.identifier(), this.actionType.getString());
    query.put(FileQuery.TOKEN.identifier(), Settings.get(Setting.TOKEN));
    query.put(FileQuery.TASK.identifier(), clientStatus.getTask().getTaskId());
    query.put(FileQuery.FILENAME.identifier(), mapping.get(MappingType.FILENAME));
    Request request = new Request();
    request.setQuery(query);
    JSONObject answer = request.execute();
    if (answer.get(FileResponse.RESPONSE.identifier()) == null) {
      LoggerFactory.getLogger().log(LogLevel.FATAL, "Got invalid message from server!");
      LoggerFactory.getLogger().log(LogLevel.DEBUG, answer.toString());
    } else if (!answer.get(FileResponse.RESPONSE.identifier()).equals("SUCCESS")) {
      LoggerFactory.getLogger().log(LogLevel.ERROR, "File download failed: " + answer.get(ErrorResponse.MESSAGE.identifier()));
      return new JSONObject();
    }
    
    String downloadUrl = (String)answer.get(FileResponse.URL.identifier());
    Utils.downloadFile(downloadUrl, "files/" + mapping.get(MappingType.FILENAME));
    
    File check = new File("files/" + mapping.get(MappingType.FILENAME));
    String[] splitted = ((String)mapping.get(MappingType.FILENAME)).split("\\.");
    String extension = splitted[splitted.length - 1];
    if(check.exists() && extension.equals("7z")){
      List<String> cmd = new ArrayList<>();
      cmd.add("7z");
      cmd.add("x");
      cmd.add("files/" + mapping.get(MappingType.FILENAME));
      cmd.add("-ofiles");
      ProcessBuilder processBuilder = new ProcessBuilder();
      processBuilder.command(cmd);
      Process process = processBuilder.start();
      InputStream is = process.getInputStream();
      InputStreamReader isr = new InputStreamReader(is);
      BufferedReader br = new BufferedReader(isr);
      String line;
      LoggerFactory.getLogger().log(LogLevel.NORMAL, "Extracting " + check.getName() + "...");
      while((line = br.readLine()) != null) {
        LoggerFactory.getLogger().log(LogLevel.DEBUG, line);
      }
    }
    
    return answer;
  }
}
