package org.hashes.hashtopussy.agent.actions;

enum ActionType {
  REGISTER {
    @Override
    public String getString() {
      return "register";
    }
  },
  LOGIN {
    @Override
    public String getString() {
      return "login";
    }
  },
  TASK {
    @Override
    public String getString() {
      return "task";
    }
  },
  CHUNK {
    @Override
    public String getString() {
      return "chunk";
    }
  },
  KEYSPACE {
    @Override
    public String getString() {
      return "keyspace";
    }
  },
  BENCHMARK {
    @Override
    public String getString() {
      return "bench";
    }
  },
  DOWNLOAD {
    @Override
    public String getString() {
      return "down";
    }
  },
  HASHLIST {
    @Override
    public String getString() {
      return "hashes";
    }
  },
  FILE {
    @Override
    public String getString() {
      return "file";
    }
  }, CRACKING {
    @Override
    public String getString() {
      return "solve";
    }
  };
  
  public abstract String getString();
  
  public boolean isStringType(String type) {
    return type.equals(getString());
  }
}
