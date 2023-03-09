# Testing
## Setup - Linux
Currently the testing of the agent is limited and a bit complicated. Once APIv2 is release the testing framework
can be extended.

1. Start the development container for the server, make sure you use the branch: feature/apiv2.
2. Start the development container for the agent.
3. Start the agent once to setup the config.json file (Run -> Start Debugging).
4. Set the agent to CPU only.
5. You should be able to run the tests with `python3 -m pytest` or run them directly from 'Testing' in VSCode.

## Setup - Windows - Docker
Currently you cannot run the tests from a devcontainer on Windows, because vscode does not support devcontainers running on Windows containers.

Only possible to run tests on a Windows platform.
Does not really allow to run tests windows hashcat, no GPU support

1. Start the development container for the server, make sure you use the branch: feature/apiv2.
2. Git clone the repo into the Windows file system
3. Switch Docker Desktop to Windows Containers. Right click the Docker Desktop tray icon. Select 'Switch to Windows Containers'
4. Open powershell, cd to the agent folder `.devcontainer\windows`
5. `docker compose build`
6. `docker compose up`
7. Everything should install, now attach to the container `docker exec -it hashtopolis_agent_windows cmd.exe`
8. Start the agent once `python -d . --url http://host.docker.internal:8080/api/server.php --debug --voucher devvoucher`
9. Run the tests `python -m pytest`

## Setup - Windows - locally

Requires some OpenCL device for example a GPU to run tests.

1. Start the development container for the server, make sure you use the branch: feature/apiv2.
2. Git clone the repo into the Windows file system
3. Install Python3.10 through https://www.python.org/downloads/ (as Admin/systemwide) + add python to path
4. Install requirements-test.txt and requirements.txt `pip3 install -r .\requirements-tests.txt -r .\requirements.txt`
5. Run VSCode install Python extension
6. Run agent once `python -d . --url http://127.0.0.1:8080/api/server.php --debug --voucher devvoucher`
7. You should be able to run the tests with `python3 -m pytest` or run them directly from 'Testing' in VSCode.

## Debugging

1. Clear the who database through Config -> Server -> Delete all
2. Check if the agent is still active
3. Clear the agent folder
4. Check if the agent is marked CPU only

## Limitations
1. Only one environment can be tested at a time.
2. Only works with APIv2.
3. No support yet for Github actions, waiting for release of APIv2 to prevent having to fix it again.