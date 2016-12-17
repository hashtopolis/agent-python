package org.hashes.hashtopussy.agent.common;

public enum Setting {
  URL {
    public String getDefault() {
      return "https://alpha.hashes.org/src/api/server.php";
    }
    
    @Override
    public Object parse(Object in) {
      return in.toString();
    }
  },
  TOKEN {
    public String getDefault() {
      return null;
      //return "SPx1G7WWPp";
    }
    
    @Override
    public Object parse(Object in) {
      return in.toString();
    }
  },
  LOGGER {
    public LoggerType getDefault() {
      return LoggerType.STDOUT;
    }
    
    @Override
    public Object parse(Object in) {
      return LoggerType.valueOf(in.toString());
    }
  },
  LOG_LEVEL {
    public LogLevel getDefault() {
      return LogLevel.DEBUG;
    }
    
    @Override
    public Object parse(Object in) {
      return LogLevel.valueOf(in.toString());
    }
  },
  DISABLE_HASHCAT_CHECK {
    public Boolean getDefault() {
      return false;
    }
    
    @Override
    public Object parse(Object in) {
      return Boolean.valueOf(in.toString());
    }
  },
  DISABLE_AUTO_UPDATE {
    public Boolean getDefault() {
      return false;
    }
    
    @Override
    public Object parse(Object in) {
      return Boolean.valueOf(in.toString());
    }
  },
  EXPERIMENTAL_BENCHMARK {
    public Boolean getDefault() {
      return false;
    }
    
    @Override
    public Object parse(Object in) {
      return Boolean.valueOf(in.toString());
    }
  };
  
  public abstract Object getDefault();
  
  public abstract Object parse(Object in);
}
