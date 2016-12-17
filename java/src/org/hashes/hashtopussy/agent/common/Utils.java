package org.hashes.hashtopussy.agent.common;

import org.hashes.hashtopussy.agent.objects.Chunk;
import org.hashes.hashtopussy.agent.objects.Task;
import org.json.JSONArray;
import org.json.JSONObject;

/**
 * Created by sein on 17.12.16.
 */
public class Utils {
  public static int[] jsonToArray(JSONArray json){
    int[] arr = new int[json.length()];
    for(int i=0;i<json.length();i++){
      arr[i] = json.getInt(i);
    }
    return arr;
  }
  
  public static void printTaskInfo(Task task){
    //TODO: make some fancy output here
    LoggerFactory.getLogger().log(LogLevel.DEBUG, "Task info: " + task.getAttackCmd() + " " + task.getCmdPars() + " " + task.getHashlistId());
  }
  
  public static void printChunkInfo(Chunk chunk){
    //TODO: make some fancy output ehre
    LoggerFactory.getLogger().log(LogLevel.DEBUG, "Chunk info: " + chunk.getChunkId() + " " + chunk.getSkip() + " " + chunk.getLength());
  }
}
