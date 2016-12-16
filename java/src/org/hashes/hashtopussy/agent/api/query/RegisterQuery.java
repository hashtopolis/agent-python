package org.hashes.hashtopussy.agent.api.query;

/**
 * Created by sein on 15.12.16.
 */
public enum RegisterQuery {
  ACTION {
    @Override
    public String identifier() {
      return "action";
    }
  },
  VOUCHER {
    @Override
    public String identifier() {
      return "voucher";
    }
  },
  UID {
    @Override
    public String identifier() {
      return "uid";
    }
  },
  NAME {
    @Override
    public String identifier() {
      return "name";
    }
  },
  OS {
    @Override
    public String identifier() {
      return "os";
    }
  },
  GPUS {
    @Override
    public String identifier() {
      return "gpus";
    }
  };
  
  public abstract String identifier();
}
