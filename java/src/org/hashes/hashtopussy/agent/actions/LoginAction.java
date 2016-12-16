package org.hashes.hashtopussy.agent.actions;

import org.hashes.hashtopussy.agent.api.response.ErrorResponse;
import org.hashes.hashtopussy.agent.api.query.LoginQuery;
import org.hashes.hashtopussy.agent.api.response.LoginResponse;
import org.hashes.hashtopussy.agent.common.LogLevel;
import org.hashes.hashtopussy.agent.common.LoggerFactory;
import org.hashes.hashtopussy.agent.common.Setting;
import org.hashes.hashtopussy.agent.common.Settings;
import org.hashes.hashtopussy.agent.exceptions.InvalidQueryException;
import org.hashes.hashtopussy.agent.exceptions.InvalidUrlException;
import org.hashes.hashtopussy.agent.exceptions.WrongResponseCodeException;
import org.hashes.hashtopussy.agent.api.Request;
import org.json.JSONObject;

import java.io.IOException;
import java.util.Map;

/**
 * Created by sein on 15.12.16.
 */
public class LoginAction extends AbstractAction {
  
  public LoginAction() {
    this.actionType = ActionType.LOGIN;
  }
  
  @Override
  public JSONObject act(Map<MappingType, Object> mapping) throws WrongResponseCodeException, InvalidQueryException, InvalidUrlException, IOException {
    String token = (String) Settings.get(Setting.TOKEN);
    if (token == null) {
      throw new IllegalArgumentException("Token must not be null on login!");
    }
    
    JSONObject query = new JSONObject();
    query.put(LoginQuery.ACTION.identifier(), this.actionType.getString());
    query.put(LoginQuery.TOKEN.identifier(), token);
    Request request = new Request();
    request.setQuery(query);
    JSONObject answer = request.execute();
    if (answer.get(LoginResponse.RESPONSE.identifier()) == null) {
      LoggerFactory.getLogger().log(LogLevel.FATAL, "Got invalid message from server!");
      LoggerFactory.getLogger().log(LogLevel.DEBUG, answer.toString());
    } else if (!answer.get(LoginResponse.RESPONSE.identifier()).equals("SUCCESS")) {
      LoggerFactory.getLogger().log(LogLevel.ERROR, "Login failed: " + answer.get(ErrorResponse.MESSAGE.identifier()));
      return new JSONObject();
    }
    LoggerFactory.getLogger().log(LogLevel.NORMAL, "Logged in successful");
    LoggerFactory.getLogger().log(LogLevel.INFO, "Logged in with timeout: " + answer.get(LoginResponse.TIMEOUT.identifier()));
    return answer;
  }
}
