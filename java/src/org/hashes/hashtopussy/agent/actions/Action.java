package org.hashes.hashtopussy.agent.actions;

import org.json.JSONObject;

import java.util.Map;

/**
 * Created by sein on 15.12.16.
 */
public interface Action {
    JSONObject act(Map<MappingType, Object> mapping) throws Exception;
}
