package org.hashes.hashtopussy.agent.api.query;

public enum CrackingQuery {
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
  },
  CHUNK {
    @Override
    public String identifier() {
      return "chunk";
    }
  },
  KPROGRESS {
    @Override
    public String identifier() {
      return "keyspaceProgress";
    }
  },
  PROGRESS {
    @Override
    public String identifier() {
      return "progress";
    }
  },
  TOTAL {
    @Override
    public String identifier() {
      return "total";
    }
  },
  SPEED {
    @Override
    public String identifier() {
      return "speed";
    }
  },
  STATE {
    @Override
    public String identifier() {
      return "state";
    }
  },
  CRACKS {
    @Override
    public String identifier() {
      return "cracks";
    }
  };
  
  public abstract String identifier();
}
