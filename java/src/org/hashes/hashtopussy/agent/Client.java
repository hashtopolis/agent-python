package org.hashes.hashtopussy.agent;

import org.hashes.hashtopussy.agent.actions.Action;
import org.hashes.hashtopussy.agent.actions.LoginAction;
import org.hashes.hashtopussy.agent.api.response.LoginResponse;
import org.hashes.hashtopussy.agent.cli.CommandLineParser;
import org.hashes.hashtopussy.agent.common.ClientStatus;
import org.hashes.hashtopussy.agent.common.LogLevel;
import org.hashes.hashtopussy.agent.common.LoggerFactory;
import org.json.JSONObject;

/**
 * Created by sein on 03.12.16.
 */
public class Client {
    public boolean isRunning;
    private ClientStatus clientStatus;

    public Client() {
        clientStatus = new ClientStatus();
    }

    public void run(){
        try {
            LoggerFactory.getLogger().log(LogLevel.DEBUG, "Entered running loop");
            isRunning = true;
            while (isRunning) {
                if (!clientStatus.getIsLoggedin()) {
                    Action action = new LoginAction();
                    JSONObject answer = action.act(null);
                    clientStatus.setIsLoggedin(true);
                    LoggerFactory.getLogger().log(LogLevel.INFO, "Logged in with timeout: " + answer.get(LoginResponse.TIMEOUT.identifier()));
                }
                //TODO: do run
            }
            LoggerFactory.getLogger().log(LogLevel.NORMAL, "HTP Client loop finished");
        } catch (Exception e){
            LoggerFactory.getLogger().log(LogLevel.FATAL, e.getClass() + " -> " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        new CommandLineParser().parse(args);

        //TODO: load settings

        new Client().run();
    }
}
