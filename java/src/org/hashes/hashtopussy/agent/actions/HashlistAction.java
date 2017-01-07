package org.hashes.hashtopussy.agent.actions;

import org.hashes.hashtopussy.agent.api.Request;
import org.hashes.hashtopussy.agent.api.query.BenchmarkQuery;
import org.hashes.hashtopussy.agent.api.query.HashlistQuery;
import org.hashes.hashtopussy.agent.api.response.BenchmarkResponse;
import org.hashes.hashtopussy.agent.api.response.ErrorResponse;
import org.hashes.hashtopussy.agent.api.response.HashlistResponse;
import org.hashes.hashtopussy.agent.api.response.KeyspaceResponse;
import org.hashes.hashtopussy.agent.common.*;
import org.hashes.hashtopussy.agent.exceptions.InvalidQueryException;
import org.hashes.hashtopussy.agent.exceptions.InvalidUrlException;
import org.hashes.hashtopussy.agent.exceptions.WrongResponseCodeException;
import org.json.JSONObject;

import java.io.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

public class HashlistAction extends AbstractAction {
  
  public HashlistAction() {
    this.actionType = ActionType.HASHLIST;
  }
  
  @Override
  public JSONObject act(Map<MappingType, Object> mapping) throws WrongResponseCodeException, InvalidQueryException, InvalidUrlException, IOException {
    ClientStatus clientStatus = ((ClientStatus) mapping.get(MappingType.CLIENTSTATUS));
  
    File folder = new File("hashlists");
    if(!folder.exists()){
      folder.mkdirs();
    }
    
    // send hashlist request to server
    JSONObject query = new JSONObject();
    query.put(HashlistQuery.ACTION.identifier(), this.actionType.getString());
    query.put(HashlistQuery.TOKEN.identifier(), Settings.get(Setting.TOKEN));
    query.put(HashlistQuery.HASHLIST.identifier(), clientStatus.getTask().getHashlistId());
    Request request = new Request();
    request.setQuery(query);
    JSONObject answer = request.execute(true, "hashlists/" + clientStatus.getTask().getHashlistId());
    if(answer.isNull(HashlistResponse.RESPONSE.identifier())){
      // hashlist was downloaded successfully
    }
    else{
      LoggerFactory.getLogger().log(LogLevel.ERROR, "Download of hashlist failed: " + answer.toString());
      new File("hashlists/" + clientStatus.getTask().getHashlistId()).delete();
      return new JSONObject();
    }
    
    return answer;
  }
}
