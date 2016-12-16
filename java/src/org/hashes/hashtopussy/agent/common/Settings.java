package org.hashes.hashtopussy.agent.common;

import org.json.JSONObject;

import java.io.*;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

/**
 * Created by sein on 15.12.16.
 */
public class Settings {
    private static Map<Setting, Object> map = new HashMap<>();
    private static final String filename = "settings.json";

    static {
        File settingsFile = new File(filename);
        if (settingsFile.exists()) {
            try {
                FileInputStream fis = new FileInputStream(settingsFile);
                byte[] data = new byte[(int) settingsFile.length()];
                fis.read(data);
                fis.close();

                JSONObject settingList = new JSONObject(new String(data, "UTF-8"));
                Iterator<String> keys = settingList.keys();
                while (keys.hasNext()) {
                    String key = keys.next();
                    try {
                        Setting setting = Setting.valueOf(key);
                        LoggerFactory.getLogger().log(LogLevel.DEBUG, "Loaded setting (" + key + "): " + settingList.get(key));
                        map.put(setting, setting.parse(settingList.get(key)));
                    } catch (IllegalArgumentException e) {
                        LoggerFactory.getLogger().log(LogLevel.WARN, "Invalid setting property: " + key);
                    }
                }
            } catch (FileNotFoundException e) {
                LoggerFactory.getLogger().log(LogLevel.ERROR, "Could not open settings file!");
            } catch (UnsupportedEncodingException e) {
                LoggerFactory.getLogger().log(LogLevel.ERROR, "Was not able to read settings file encoding!");
            } catch (IOException e) {
                LoggerFactory.getLogger().log(LogLevel.ERROR, "Failed to read settings file!");
            }
        }
        LoggerFactory.getLogger().setLevel((LogLevel) map.get(Setting.LOG_LEVEL));
    }

    public static void set(Setting setting, Object value) {
        if (map.get(setting) != null) {
            map.replace(setting, value);
        } else {
            map.put(setting, value);
        }

        File settingsFile = new File(filename);
        JSONObject settingList = new JSONObject();
        Iterator it = map.entrySet().iterator();
        while (it.hasNext()) {
            Map.Entry pair = (Map.Entry) it.next();
            settingList.put(pair.getKey().toString(), pair.getValue());
        }
        try {
            PrintWriter out = new PrintWriter(settingsFile);
            out.print(settingList.toString());
            out.flush();
            out.close();
        } catch (FileNotFoundException e) {
            LoggerFactory.getLogger().log(LogLevel.ERROR, "Failed to save updated settings!");
        }
    }

    public static Object get(Setting setting) {
        if (map.get(setting) == null) {
            return setting.getDefault();
        }
        return map.get(setting);
    }
}
