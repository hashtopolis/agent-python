FROM alpine/git AS preprocess

RUN apk add --no-cache bash zip

COPY . /htp

RUN cd /htp && bash build.sh && ls /htp

FROM nvidia/cuda:12.3.2-devel-ubuntu22.04 AS agent-cuda

ENV APPDIR=/htp-agent

WORKDIR ${APPDIR}

RUN \
  --mount=type=cache,target=/var/cache/apt \
  apt-get update && apt-get install -y --no-install-recommends \
  zip \
  p7zip-full \
  git \
  python3 \
  python3-pip \
  python3-psutil \
  python3-requests \
  pciutils \
  ca-certificates \
  rsync \
  ocl-icd-libopencl1 \
  clinfo \
  curl && \
  rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/OpenCL/vendors && \
    echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd && \
    echo "/usr/local/nvidia/lib" >> /etc/ld.so.conf.d/nvidia.conf && \
    echo "/usr/local/nvidia/lib64" >> /etc/ld.so.conf.d/nvidia.conf

ENV PATH=/usr/local/nvidia/bin:${PATH}
ENV LD_LIBRARY_PATH=/usr/local/nvidia/lib:/usr/local/nvidia/lib64:${LD_LIBRARY_PATH}

COPY --from=preprocess /htp/hashtopolis.zip ${APPDIR}/


RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "hashtopolis.zip"]
