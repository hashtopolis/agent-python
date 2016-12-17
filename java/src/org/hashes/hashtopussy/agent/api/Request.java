package org.hashes.hashtopussy.agent.api;

import org.hashes.hashtopussy.agent.common.Setting;
import org.hashes.hashtopussy.agent.common.Settings;
import org.hashes.hashtopussy.agent.exceptions.InvalidQueryException;
import org.hashes.hashtopussy.agent.exceptions.InvalidUrlException;
import org.hashes.hashtopussy.agent.exceptions.WrongResponseCodeException;
import org.json.*;

import javax.net.ssl.HttpsURLConnection;
import java.io.BufferedReader;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.URL;

public class Request {
  private String url;
  private JSONObject query;
  
  public Request() {
    this.url = (String) Settings.get(Setting.URL);
  }
  
  public void setQuery(JSONObject query) {
    this.query = query;
  }
  
  public JSONObject execute() throws InvalidQueryException, InvalidUrlException, IOException, WrongResponseCodeException {
    if (this.query == null) {
      throw new InvalidQueryException("Query arguments cannot be null!");
    } else if (this.url == null) {
      throw new InvalidUrlException("URL cannot be null!");
    }
    
    URL obj = new URL(this.url);
    HttpsURLConnection con = (HttpsURLConnection) obj.openConnection();
    
    // set request header
    con.setRequestMethod("POST");
    con.setRequestProperty("User-Agent", "HTP Client/1");
    con.setRequestProperty("Accept-Language", "en-US,en;q=0.5");
    
    String urlParameters = "query=" + this.query.toString();
    
    // send post request
    con.setDoOutput(true);
    DataOutputStream wr = new DataOutputStream(con.getOutputStream());
    wr.writeBytes(urlParameters);
    wr.flush();
    wr.close();
    
    int responseCode = con.getResponseCode();
    if (responseCode != 200) {
      throw new WrongResponseCodeException("Got response code: " + responseCode);
    }
    
    // read answer
    BufferedReader in = new BufferedReader(new InputStreamReader(con.getInputStream()));
    String inputLine;
    StringBuffer response = new StringBuffer();
    while ((inputLine = in.readLine()) != null) {
      response.append(inputLine);
    }
    in.close();
    
    return new JSONObject(response.toString());
  }
}
