FROM ubuntu:20.04

ARG DEV_CONTAINER_USER_CMD_PRE
ARG DEV_CONTAINER_USER_CMD_POST

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive
ENV NODE_OPTIONS='--use-openssl-ca'

# Check for and run optional user-supplied command to enable (advanced) customizations of the dev container
RUN if [ -n "${DEV_CONTAINER_USER_CMD_PRE}" ]; then echo "${DEV_CONTAINER_USER_CMD_PRE}" | sh ; fi

RUN groupadd vscode && useradd -rm -d /app -s /bin/bash -g vscode -u 1001 vscode

RUN apt-get update \
    && apt-get install python3 python3-pip -y \
    && apt-get install git -y 

# Install Intel OpenCL Runtime
RUN cd /tmp \
    && apt install wget lsb-core libnuma-dev pciutils clinfo -y \
    && wget -O- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB | gpg --dearmor | tee /usr/share/keyrings/oneapi-archive-keyring.gpg >/dev/null \
    && echo "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main"  | tee /etc/apt/sources.list.d/oneAPI.list \
    && apt update \
    && apt install intel-oneapi-runtime-libs opencl-headers -y

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
COPY requirements-tests.txt /app/src/
RUN /usr/bin/pip3 install -r src/requirements.txt
RUN /usr/bin/pip3 install -r src/requirements-tests.txt

# Check for and run optional user-supplied command to enable (advanced) customizations of the dev container
RUN if [ -n "${DEV_CONTAINER_USER_CMD_POST}" ]; then echo "${DEV_CONTAINER_USER_CMD_POST}" | sh ; fi

# Preventing container from exiting
CMD tail -f /dev/null
