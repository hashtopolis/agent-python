package org.hashes.hashtopussy.agent;

import org.hashes.hashtopussy.agent.actions.Action;
import org.hashes.hashtopussy.agent.actions.LoginAction;
import org.hashes.hashtopussy.agent.common.LogLevel;
import org.hashes.hashtopussy.agent.common.LoggerFactory;
import org.json.JSONObject;

/**
 * Created by sein on 03.12.16.
 */
public class Client {
    public Client() {

    }

    public static void main(String[] args) {
        //TODO: parse command line
        //TODO: load settings
        //TODO: start loop

        // example action
        Action action = new LoginAction();
        JSONObject answer = action.act(null);
        LoggerFactory.getLogger().log(LogLevel.INFO, "Logged in with timeout: " + answer.get("timeout"));
    }
}
