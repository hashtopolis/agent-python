package org.hashes.hashtopussy.agent.actions;

import org.hashes.hashtopussy.agent.common.*;
import org.json.JSONObject;

import java.util.Map;

public class DownloadAction extends AbstractAction {
  
  public DownloadAction() {
    this.actionType = ActionType.DOWNLOAD;
  }
  
  @Override
  public JSONObject act(Map<MappingType, Object> mapping) throws Exception {
    ClientStatus clientStatus = ((ClientStatus) mapping.get(MappingType.CLIENTSTATUS));
    
    // download hashlist
    Action action = new HashlistAction();
    action.act(mapping);
    
    // download files
    for(String f: clientStatus.getTask().getFiles()){
      action = new FileAction();
      mapping.remove(MappingType.FILENAME);
      mapping.put(MappingType.FILENAME, f);
      action.act(mapping);
    }
    
    return null;
  }
}
