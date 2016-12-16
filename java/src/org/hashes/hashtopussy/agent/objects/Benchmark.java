package org.hashes.hashtopussy.agent.objects;

/**
 * Created by sein on 16.12.16.
 */
public class Benchmark {
    private boolean isExperimental;
    private String result;

    public Benchmark(String result, boolean isExperimental){
        this.result = result;
        this.isExperimental = isExperimental;
    }

    public boolean getIsExperimental(){
        return isExperimental;
    }

    public String getResult(){
        return result;
    }
}
