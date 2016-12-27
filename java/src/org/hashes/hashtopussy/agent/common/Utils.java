package org.hashes.hashtopussy.agent.common;

import org.hashes.hashtopussy.agent.objects.Chunk;
import org.hashes.hashtopussy.agent.objects.Task;
import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

public class Utils {
  public static int[] jsonToArray(JSONArray json) {
    int[] arr = new int[json.length()];
    for (int i = 0; i < json.length(); i++) {
      arr[i] = json.getInt(i);
    }
    return arr;
  }
  
  public static void printTaskInfo(Task task) {
    //TODO: make some fancy output here
    LoggerFactory.getLogger().log(LogLevel.DEBUG, "Task info: " + task.getAttackCmd() + " " + task.getCmdPars() + " " + task.getHashlistId());
  }
  
  public static void printChunkInfo(Chunk chunk) {
    //TODO: make some fancy output ehre
    LoggerFactory.getLogger().log(LogLevel.DEBUG, "Chunk info: " + chunk.getChunkId() + " " + chunk.getSkip() + " " + chunk.getLength());
  }
  
  public static boolean is64bitArchitecture(){
    boolean is64bit;
    if (System.getProperty("os.name").contains("Windows")) {
      is64bit = (System.getenv("ProgramFiles(x86)") != null);
    } else {
      is64bit = (System.getProperty("os.arch").indexOf("64") != -1);
    }
    return is64bit;
  }
  
  public static List<String> splitArguments(String args){
    List<String> list = new ArrayList<>();
    String current = "";
    for(int i=0;i<args.length();i++){
      if(args.charAt(i) == ' '){
        if((i > 0 && args.charAt(i-1) != '\\') || i == 0){
          if(current.length() > 0) {
            list.add(current);
          }
          current = "";
        }
        else{
          current += args.charAt(i);
        }
      }
      else {
        current += args.charAt(i);
      }
    }
    if(current.length() > 0){
      list.add(current);
    }
    return list;
  }
}
