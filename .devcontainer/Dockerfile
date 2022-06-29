FROM ubuntu:20.04

ARG DEV_CONTAINER_USER_CMD

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Check for and run optional user-supplied command to enable (advanced) customizations of the dev container
RUN if [ -n "${DEV_CONTAINER_USER_CMD}" ]; then echo "${DEV_CONTAINER_USER_CMD}" | sh ; fi

RUN groupadd vscode && useradd -rm -d /app -s /bin/bash -g vscode -u 1001 vscode

RUN apt-get update \
    && apt-get install python3 python3-pip -y \
    && apt-get install git -y 

# Install Intel OpenCL Runtime
RUN cd /tmp \
    && apt install wget lsb-core libnuma-dev pciutils -y \
    && wget http://registrationcenter-download.intel.com/akdlm/irc_nas/vcp/15532/l_opencl_p_18.1.0.015.tgz \
    && tar xzvf l_opencl_p_18.1.0.015.tgz \
    && cd l_opencl_p_18.1.0.015 \
    && echo "ACCEPT_EULA=accept" > silent.cfg \
    && echo "PSET_INSTALL_DIR=/opt/intel" >> silent.cfg \
    && echo "CONTINUE_WITH_OPTIONAL_ERROR=yes" >> silent.cfg \
    && echo "CONTINUE_WITH_INSTALLDIR_OVERWRITE=yes" >> silent.cfg \
    && echo "COMPONENTS=DEFAULTS" >> silent.cfg \
    && echo "PSET_MODE=install" >> silent.cfg \
    && ./install.sh -s silent.cfg

# Clean
RUN apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/l_opencl_p_18.1.0.015*

# Switch back to dialog for any ad-hoc use of apt-get
ENV DEBIAN_FRONTEND=dialog

# Configuring app / python requirements
WORKDIR /app
USER vscode
COPY requirements.txt /app/src/
RUN /usr/bin/pip3 install -r src/requirements.txt

# Preventing container from exiting
CMD tail -f /dev/null
