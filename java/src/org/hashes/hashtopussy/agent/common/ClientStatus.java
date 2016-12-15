package org.hashes.hashtopussy.agent.common;

/**
 * Created by sein on 15.12.16.
 */
public class ClientStatus {
    private boolean isLoggedin = false;

    public void setIsLoggedin(boolean isLoggedin){
        this.isLoggedin = isLoggedin;
    }

    public boolean getIsLoggedin(){
        return isLoggedin;
    }
}
