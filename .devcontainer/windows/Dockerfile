FROM mcr.microsoft.com/windows-cssc/python3.7.2server:ltsc2022
# Nano image doesn't work because some API are not available

# TODO: Support for USER_CMD_PRE and POST?
# TODO: Create a vscode user?
# TODO: OpenCL/Nvidia?

WORKDIR C:/App/

# Installing python requirements
COPY requirements.txt C:/App/
COPY requirements-tests.txt C:/App/
RUN pip3 install -r requirements.txt -r requirements-tests.txt

# Fix for host.docker.internal not working
COPY .devcontainer/windows/entrypoint.ps1 C:/
COPY .devcontainer/windows/fix-hosts.ps1 C:/

# Setting entrypoint
ENTRYPOINT "C:\entrypoint.ps1"
