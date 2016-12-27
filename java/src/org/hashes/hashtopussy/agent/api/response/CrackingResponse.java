package org.hashes.hashtopussy.agent.api.response;

public enum CrackingResponse {
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
  CRACKED {
    @Override
    public String identifier() {
      return "cracked";
    }
  },
  SKIPPED {
    @Override
    public String identifier() {
      return "skipped";
    }
  },
  ZAP {
    @Override
    public String identifier() {
      return "zap";
    }
  };
  
  public abstract String identifier();
}
