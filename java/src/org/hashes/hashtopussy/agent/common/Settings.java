package org.hashes.hashtopussy.agent.common;

import java.io.PrintWriter;
import java.util.HashMap;
import java.util.Map;

/**
 * Created by sein on 15.12.16.
 */
public class Settings {
    private static Map<Setting, Object> map = new HashMap<Setting, Object>();

    public static void set(Setting setting, Object value){
        if(map.get(setting) != null){
            map.replace(setting, value);
        }
        else {
            map.put(setting, value);
        }
    }

    public static Object get(Setting setting){
        if(map.get(setting) == null){
            return setting.getDefault();
        }
        return map.get(setting);
    }
}
