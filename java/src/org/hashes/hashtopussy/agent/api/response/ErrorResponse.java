package org.hashes.hashtopussy.agent.api.response;

/**
 * Created by sein on 15.12.16.
 */
public enum ErrorResponse {
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
    MESSAGE {
        @Override
        public String identifier() {
            return "message";
        }
    };

    public abstract String identifier();
}
