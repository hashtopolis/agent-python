package org.hashes.hashtopussy.agent.api.response;

/**
 * Created by sein on 16.12.16.
 */
public enum RegisterResponse {
    ACTION {
        @Override
        public String identifier() {
            return "action";
        }
    },
    RESPONSE {
        @Override
        public String identifier() {
            return "response";
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
