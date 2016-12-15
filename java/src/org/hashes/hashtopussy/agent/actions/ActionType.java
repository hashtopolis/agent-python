package org.hashes.hashtopussy.agent.actions;

/**
 * Created by sein on 15.12.16.
 */
enum ActionType {
    REGISTER {
        public String getString() {
            return "reg";
        }

        public boolean isStringType(String type) {
            return type.equals("reg");
        }
    },
    LOGIN {
        public String getString() {
            return "login";
        }

        public boolean isStringType(String type) {
            return type.equals("login");
        }
    };
    //TODO: add more actionTypes

    public abstract String getString();

    public abstract boolean isStringType(String type);
}
