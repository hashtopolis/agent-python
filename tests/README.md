# Testing
## Setup
Currently the testing of the agent is limited and a bit complicated. Once APIv2 is release the testing framework
can be extended.

1. Start the development container for the server, make sure you use the branch: feature/apiv2
2. Start the development container for the agent
3. Start the agent once to setup the config.json file
4. You should be able to run the tests with `python3 -m pytest` or run them directly from 'Testing' in VSCode

## Limitations
1. Only one environment can be tested at a time
2. Only works with APIv2
3. No support yet for Github actions, waiting for release of APIv2 to prevent having to fix it again.