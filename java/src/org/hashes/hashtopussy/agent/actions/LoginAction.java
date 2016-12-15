package org.hashes.hashtopussy.agent.actions;

import org.hashes.hashtopussy.agent.common.LogLevel;
import org.hashes.hashtopussy.agent.common.LoggerFactory;
import org.hashes.hashtopussy.agent.common.Settings;
import org.hashes.hashtopussy.agent.exceptions.InvalidQueryException;
import org.hashes.hashtopussy.agent.exceptions.InvalidUrlException;
import org.hashes.hashtopussy.agent.exceptions.WrongResponseCodeException;
import org.hashes.hashtopussy.agent.request.Request;
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

    public JSONObject act(Map<MappingType, Object> mapping) {
        String token = Settings.getToken();
        if (token == null) {
            throw new IllegalArgumentException("Token must not be null on login!");
        }

        JSONObject answer = new JSONObject();
        try {
            JSONObject query = new JSONObject();
            query.put("action", this.actionType.getString());
            query.put("token", token);
            Request request = new Request(Settings.getUrl());
            request.setQuery(query);
            answer = request.execute();
            if (answer.get("response") == null) {
                LoggerFactory.getLogger().log(LogLevel.FATAL, "Got invalid message from server!");
                LoggerFactory.getLogger().log(LogLevel.DEBUG, answer.toString());
            } else if (!answer.get("response").equals("SUCCESS")) {
                LoggerFactory.getLogger().log(LogLevel.ERROR, "Login failed: " + answer.get("message"));
                return new JSONObject();
            }
            LoggerFactory.getLogger().log(LogLevel.NORMAL, "Logged in successful");
        } catch (InvalidQueryException e) {
            e.printStackTrace();
        } catch (InvalidUrlException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        } catch (WrongResponseCodeException e) {
            e.printStackTrace();
        }
        return answer;
    }
}
