package org.hashes.hashtopussy.agent.api.query;

/**
 * Created by sein on 15.12.16.
 */
public enum LoginQuery {
    ACTION {
        @Override
        public String identifier() {
            return "action";
        }
    },
    TOKEN {
        @Override
        public String identifier() {
            return "token";
        }
    };

    public abstract String identifier();
}
