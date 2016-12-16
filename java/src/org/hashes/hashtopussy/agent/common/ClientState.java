package org.hashes.hashtopussy.agent.common;

/**
 * Created by sein on 16.12.16.
 */
public enum ClientState {
  INIT,
  LOGIN_READY,
  LOGIN_DONE,
  TASK_RECEIVED,
  CHUNK_RECEIVED,
  BENCHMARK_REQUIRED,
  KEYSPACE_REQUIRED,
  ERROR
}
