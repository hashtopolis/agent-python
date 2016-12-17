package org.hashes.hashtopussy.agent.common;

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
