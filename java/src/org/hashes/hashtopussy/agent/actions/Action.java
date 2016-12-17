package org.hashes.hashtopussy.agent.actions;

import org.json.JSONObject;

import java.util.Map;

public interface Action {
  JSONObject act(Map<MappingType, Object> mapping) throws Exception;
}
