# Java Agent

WARNING: This PHP Agent is neither complete nor thought to be used as productive agent for cracking with Hashtopussy.

## Usage

TODO: set some parameters when running...

```
java -jar htp-agent.jar
```

## Building

To build the jar from source, you just need to run the gradle deploy:

```
./gradlew deploy
```

The jar will be placed in ```build/libs/``` then.

## Settings

Settings for the client are saved in ```settings.json```. If you set some command line arguments they will also get saved there, so the next run you don't have to add them anymore. If you want to change values, you can either edit the settings file directly (but make sure that the values are valid) or you can set the command line arguments to the new value you want to have it set to, then the values will get replaced.
