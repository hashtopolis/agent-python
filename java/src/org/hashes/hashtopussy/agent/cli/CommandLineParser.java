package org.hashes.hashtopussy.agent.cli;

import org.hashes.hashtopussy.agent.common.*;

public class CommandLineParser {
  public void parse(String[] argv) {
    try {
      for (int x = 0; x < argv.length; x++) {
        switch (argv[x]) {
          case "--experimental-bench":
            Settings.set(Setting.EXPERIMENTAL_BENCHMARK, true);
            break;
          case "--nocheck":
            Settings.set(Setting.DISABLE_HASHCAT_CHECK, true);
            break;
          case "--noupdate":
            Settings.set(Setting.DISABLE_AUTO_UPDATE, true);
            break;
          case "--logger":
            if (x + 2 > argv.length) {
              throw new IllegalArgumentException("--logger needs a value!");
            }
            try {
              Settings.set(Setting.LOGGER, LoggerType.valueOf(argv[x + 1].toUpperCase()));
            } catch (IllegalArgumentException e) {
              throw new IllegalArgumentException("Invalid log level!");
            }
          case "--log-level":
            if (x + 2 > argv.length) {
              throw new IllegalArgumentException("--log-level needs a value!");
            }
            try {
              Settings.set(Setting.LOG_LEVEL, LogLevel.valueOf(argv[x + 1].toUpperCase()));
            } catch (IllegalArgumentException e) {
              throw new IllegalArgumentException("Invalid log level!");
            }
          default:
            LoggerFactory.getLogger().log(LogLevel.ERROR, "Invalid command line argument: " + argv[x]);
        }
      }
    } catch (IllegalArgumentException e) {
      LoggerFactory.getLogger().log(LogLevel.FATAL, "Command line parsing failed! " + e.getMessage());
    }
  }
}
