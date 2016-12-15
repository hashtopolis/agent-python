package org.hashes.hashtopussy.agent.common;

/**
 * Created by sein on 15.12.16.
 */
public enum Setting {
    URL {
        public String getDefault() {
            return "https://alpha.hashes.org/src/api/server.php";
        }
    },
    TOKEN {
        public String getDefault() {
            return "SPx1G7WWPp";
        }
    },
    LOGGER {
        @Override
        public LoggerType getDefault() {
            return LoggerType.STDOUT;
        }
    },
    LOG_LEVEL {
        @Override
        public LogLevel getDefault() {
            return LogLevel.NORMAL;
        }
    },
    DISABLE_HASHCAT_CHECK {
        public Boolean getDefault() {
            return false;
        }
    },
    DISABLE_AUTO_UPDATE {
        public Boolean getDefault() {
            return false;
        }
    },
    EXPERIMENTAL_BENCHMARK {
        public Boolean getDefault() {
            return false;
        }
    };

    public abstract Object getDefault();
}
