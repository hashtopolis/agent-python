package org.hashes.hashtopussy.agent.objects;

/**
 * Created by sein on 16.12.16.
 */
public class Chunk {
    private int chunkId;
    private long skip;
    private long length;

    public Chunk(int chunkId, long skip, long length){
        this.chunkId = chunkId;
        this.skip = skip;
        this.length = length;
    }

    public int getChunkId() {
        return chunkId;
    }

    public long getSkip() {
        return skip;
    }

    public long getLength() {
        return length;
    }
}
