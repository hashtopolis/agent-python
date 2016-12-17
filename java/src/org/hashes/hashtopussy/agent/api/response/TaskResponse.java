package org.hashes.hashtopussy.agent.api.response;

/**
 * Created by sein on 16.12.16.
 */
public enum TaskResponse {
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
  TASK {
    @Override
    public String identifier() {
      return "task";
    }
  },
  WAIT {
    @Override
    public String identifier() {
      return "wait";
    }
  },
  ATTACKCMD {
    @Override
    public String identifier() {
      return "attackcmd";
    }
  },
  CMDPARS {
    @Override
    public String identifier() {
      return "cmdpars";
    }
  },
  HASHLIST {
    @Override
    public String identifier() {
      return "hashlist";
    }
  },
  BENCHMARCK {
    @Override
    public String identifier() {
      return "bench";
    }
  },
  STATUSTIMER {
    @Override
    public String identifier() {
      return "statustimer";
    }
  },
  FILES {
    @Override
    public String identifier() {
      return "files";
    }
  };
  
  public abstract String identifier();
}
