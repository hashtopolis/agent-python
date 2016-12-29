package org.hashes.hashtopussy.agent.actions;

import org.hashes.hashtopussy.agent.api.Request;
import org.hashes.hashtopussy.agent.api.query.ChunkQuery;
import org.hashes.hashtopussy.agent.api.response.ChunkResponse;
import org.hashes.hashtopussy.agent.api.response.ErrorResponse;
import org.hashes.hashtopussy.agent.common.*;
import org.hashes.hashtopussy.agent.exceptions.InvalidQueryException;
import org.hashes.hashtopussy.agent.exceptions.InvalidUrlException;
import org.hashes.hashtopussy.agent.exceptions.WrongResponseCodeException;
import org.hashes.hashtopussy.agent.objects.Chunk;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.IOException;
import java.util.Map;

public class ChunkAction extends AbstractAction {
  
  public ChunkAction() {
    this.actionType = ActionType.CHUNK;
  }
  
  @Override
  public JSONObject act(Map<MappingType, Object> mapping) throws WrongResponseCodeException, InvalidQueryException, InvalidUrlException, IOException {
    ClientStatus clientStatus = ((ClientStatus) mapping.get(MappingType.CLIENTSTATUS));
    JSONObject query = new JSONObject();
    query.put(ChunkQuery.ACTION.identifier(), this.actionType.getString());
    query.put(ChunkQuery.TOKEN.identifier(), Settings.get(Setting.TOKEN));
    query.put(ChunkQuery.TASK.identifier(), clientStatus.getTask().getTaskId());
    Request request = new Request();
    request.setQuery(query);
    JSONObject answer = answer = request.execute();
    if (answer.get(ChunkResponse.RESPONSE.identifier()) == null) {
      LoggerFactory.getLogger().log(LogLevel.FATAL, "Got invalid message from server!");
      LoggerFactory.getLogger().log(LogLevel.DEBUG, answer.toString());
    } else if (!answer.get(ChunkResponse.RESPONSE.identifier()).equals("SUCCESS")) {
      LoggerFactory.getLogger().log(LogLevel.ERROR, "Getting chunk failed: " + answer.get(ErrorResponse.MESSAGE.identifier()));
      return new JSONObject();
    }
    
    //I got a correct answer
    if (answer.get(ChunkResponse.CHUNK.identifier()).equals("keyspace_required")) {
      LoggerFactory.getLogger().log(LogLevel.NORMAL, "Client needs to calculate keyspace for this task");
      clientStatus.setCurrentState(ClientState.KEYSPACE_REQUIRED);
    } else if (answer.get(ChunkResponse.CHUNK.identifier()).equals("fully_dispatched")) {
      LoggerFactory.getLogger().log(LogLevel.INFO, "Task is already fully dispatched");
    } else if (answer.get(ChunkResponse.CHUNK.identifier()).equals("benchmark")) {
      LoggerFactory.getLogger().log(LogLevel.NORMAL, "Client needs to benchmark for this task");
      clientStatus.setCurrentState(ClientState.BENCHMARK_REQUIRED);
    } else {
      Chunk chunk = new Chunk(
          answer.getInt(ChunkResponse.CHUNK.identifier()),
          answer.getLong(ChunkResponse.SKIP.identifier()),
          answer.getLong(ChunkResponse.LENGTH.identifier())
      );
      clientStatus.setChunk(chunk);
      LoggerFactory.getLogger().log(LogLevel.NORMAL, "Got chunk from server");
    }
    
    return answer;
  }
}
