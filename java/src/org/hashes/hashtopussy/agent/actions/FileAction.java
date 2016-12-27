package org.hashes.hashtopussy.agent.actions;

import jdk.jfr.events.FileReadEvent;
import org.hashes.hashtopussy.agent.api.Request;
import org.hashes.hashtopussy.agent.api.query.FileQuery;
import org.hashes.hashtopussy.agent.api.query.HashlistQuery;
import org.hashes.hashtopussy.agent.api.response.ErrorResponse;
import org.hashes.hashtopussy.agent.api.response.FileResponse;
import org.hashes.hashtopussy.agent.api.response.HashlistResponse;
import org.hashes.hashtopussy.agent.api.response.RegisterResponse;
import org.hashes.hashtopussy.agent.common.*;
import org.hashes.hashtopussy.agent.exceptions.InvalidQueryException;
import org.hashes.hashtopussy.agent.exceptions.InvalidUrlException;
import org.hashes.hashtopussy.agent.exceptions.WrongResponseCodeException;
import org.json.JSONObject;

import java.io.File;
import java.io.IOException;
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
    request = new Request(downloadUrl);
    answer = request.execute(true, "files/" + mapping.get(MappingType.FILENAME));
    
    return answer;
  }
}
