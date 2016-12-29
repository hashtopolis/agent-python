package org.hashes.hashtopussy.agent.actions;

import org.hashes.hashtopussy.agent.api.Request;
import org.hashes.hashtopussy.agent.api.query.RegisterQuery;
import org.hashes.hashtopussy.agent.api.response.ErrorResponse;
import org.hashes.hashtopussy.agent.api.response.RegisterResponse;
import org.hashes.hashtopussy.agent.common.LogLevel;
import org.hashes.hashtopussy.agent.common.LoggerFactory;
import org.hashes.hashtopussy.agent.common.Setting;
import org.hashes.hashtopussy.agent.common.Settings;
import org.hashes.hashtopussy.agent.exceptions.InvalidQueryException;
import org.hashes.hashtopussy.agent.exceptions.InvalidUrlException;
import org.hashes.hashtopussy.agent.exceptions.WrongResponseCodeException;
import org.json.JSONObject;

import java.io.IOException;
import java.util.Map;

public class RegisterAction extends AbstractAction {
  
  public RegisterAction() {
    this.actionType = ActionType.REGISTER;
  }
  
  @Override
  public JSONObject act(Map<MappingType, Object> mapping) throws WrongResponseCodeException, InvalidQueryException, InvalidUrlException, IOException {
    JSONObject query = new JSONObject();
    query.put(RegisterQuery.ACTION.identifier(), this.actionType.getString());
    query.put(RegisterQuery.VOUCHER.identifier(), mapping.get(MappingType.VOUCHER));
    
    //TODO: determine registering values for uid, os, gpus, name
    String[] gpus = {"ATI HD 7970", "GTX 1070"};
    query.put(RegisterQuery.NAME.identifier(), java.net.InetAddress.getLocalHost().getHostName());
    query.put(RegisterQuery.OS.identifier(), 0);
    query.put(RegisterQuery.UID.identifier(), "123-456-789");
    query.put(RegisterQuery.GPUS.identifier(), gpus);
    
    Request request = new Request();
    request.setQuery(query);
    JSONObject answer = request.execute();
    if (answer.get(RegisterResponse.RESPONSE.identifier()) == null) {
      LoggerFactory.getLogger().log(LogLevel.FATAL, "Got invalid message from server!");
      LoggerFactory.getLogger().log(LogLevel.DEBUG, answer.toString());
    } else if (!answer.get(RegisterResponse.RESPONSE.identifier()).equals("SUCCESS")) {
      LoggerFactory.getLogger().log(LogLevel.ERROR, "Register failed: " + answer.get(ErrorResponse.MESSAGE.identifier()));
      return new JSONObject();
    }
    Settings.set(Setting.TOKEN, answer.get(RegisterResponse.TOKEN.identifier()));
    LoggerFactory.getLogger().log(LogLevel.NORMAL, "Registered agent successfully");
    return answer;
  }
}
