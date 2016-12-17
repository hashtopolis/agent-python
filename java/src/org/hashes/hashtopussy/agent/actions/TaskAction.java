package org.hashes.hashtopussy.agent.actions;

import org.hashes.hashtopussy.agent.api.Request;
import org.hashes.hashtopussy.agent.api.query.TaskQuery;
import org.hashes.hashtopussy.agent.api.response.ErrorResponse;
import org.hashes.hashtopussy.agent.api.response.TaskResponse;
import org.hashes.hashtopussy.agent.common.*;
import org.hashes.hashtopussy.agent.exceptions.InvalidQueryException;
import org.hashes.hashtopussy.agent.exceptions.InvalidUrlException;
import org.hashes.hashtopussy.agent.exceptions.WrongResponseCodeException;
import org.hashes.hashtopussy.agent.objects.Task;
import org.json.JSONArray;
import org.json.JSONObject;

import java.io.IOException;
import java.util.Map;

public class TaskAction extends AbstractAction {
  
  public TaskAction() {
    this.actionType = ActionType.TASK;
  }
  
  @Override
  public JSONObject act(Map<MappingType, Object> mapping) throws WrongResponseCodeException, InvalidQueryException, InvalidUrlException, IOException {
    JSONObject query = new JSONObject();
    query.put(TaskQuery.ACTION.identifier(), this.actionType.getString());
    query.put(TaskQuery.TOKEN.identifier(), Settings.get(Setting.TOKEN));
    Request request = new Request();
    request.setQuery(query);
    JSONObject answer = request.execute();
    if (answer.get(TaskResponse.RESPONSE.identifier()) == null) {
      LoggerFactory.getLogger().log(LogLevel.FATAL, "Got invalid message from server!");
      LoggerFactory.getLogger().log(LogLevel.DEBUG, answer.toString());
    } else if (!answer.get(TaskResponse.RESPONSE.identifier()).equals("SUCCESS")) {
      LoggerFactory.getLogger().log(LogLevel.ERROR, "Getting task failed: " + answer.get(ErrorResponse.MESSAGE.identifier()));
      return new JSONObject();
    }
    LoggerFactory.getLogger().log(LogLevel.NORMAL, "Got task from server");
    
    if (answer.get(TaskResponse.TASK.identifier()).equals("NONE")) {
      LoggerFactory.getLogger().log(LogLevel.NORMAL, "Currently no tasks available!");
    } else {
      Task task = new Task(
          Integer.parseInt((String) answer.get(TaskResponse.TASK.identifier())),
          Integer.parseInt((String) answer.get(TaskResponse.WAIT.identifier())),
          (String) answer.get(TaskResponse.ATTACKCMD.identifier()),
          (String) answer.get(TaskResponse.CMDPARS.identifier()),
          Integer.parseInt((String) answer.get(TaskResponse.HASHLIST.identifier())),
          (String) answer.get(TaskResponse.BENCHMARCK.identifier()),
          Integer.parseInt((String) answer.get(TaskResponse.STATUSTIMER.identifier())),
          Utils.jsonToArray((JSONArray) answer.get(TaskResponse.FILES.identifier()))
      );
      ((ClientStatus) mapping.get(MappingType.CLIENTSTATUS)).setTask(task);
    }
    
    return answer;
  }
}
