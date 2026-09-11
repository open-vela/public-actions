# Copyright 2024 OpenVela
#
# This Dockerfile is based on and modified from the Apache NuttX Dockerfile
# located at: https://github.com/apache/nuttx/blob/master/tools/ci/docker/linux/Dockerfile.
#
# SPDX-License-Identifier: Apache-2.0
#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.  The
# ASF licenses this file to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance with the
# License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations
# under the License.
#
# OpenVela development and CI base image.
#
# This image intentionally installs host dependencies only. OpenVela source,
# compiler toolchains, QEMU prebuilts, CMake prebuilts, build-tools, and
# emulator prebuilts are synced by repo from open-vela/manifests.

FROM ubuntu:22.04

ARG OPENVELA_UID=1000
ARG OPENVELA_GID=1000

ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_DISABLE_PIP_VERSION_CHECK=true
ENV PIP_NO_CACHE_DIR=1
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV HOME=/home/openvela

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# For the 32-bit sim configs (CONFIG_SIM_M32=y).
RUN dpkg --add-architecture i386

RUN apt-get update -qq \
  && apt-get install -y -qq --no-install-recommends \
    autoconf \
    automake \
    bison \
    build-essential \
    ca-certificates \
    cmake \
    curl \
    dfu-util \
    flex \
    g++-12-multilib \
    gcc-12-multilib \
    genromfs \
    gettext \
    git \
    git-lfs \
    gnupg \
    gperf \
    jq \
    less \
    lsb-release \
    libasound2-dev \
    libasound2-plugins \
    libc++-dev \
    libc++abi-dev \
    libc6-dev \
    libdivsufsort-dev \
    libncurses5 \
    libprotobuf-dev \
    libpulse-dev \
    libusb-1.0-0-dev \
    libuv1-dev \
    libv4l-dev \
    libx11-dev \
    libxext-dev \
    locales \
    make \
    mtools \
    nasm \
    net-tools \
    ninja-build \
    nodejs \
    npm \
    pkgconf \
    protobuf-c-compiler \
    protobuf-compiler \
    python-is-python3 \
    python3 \
    python3-pip \
    python3-venv \
    qemu-efi-aarch64 \
    qemu-system-arm \
    qemu-system-misc \
    qemu-utils \
    rsync \
    sudo \
    u-boot-tools \
    unzip \
    wget \
    xxd \
    xz-utils \
    yasm \
    zip \
  && locale-gen C.UTF-8 \
  && git lfs install --system \
  && rm -rf /var/lib/apt/lists/*

# Own apt transaction: pulled into the main one, apt reports held broken
# packages. libunwind-dev:i386 must not be used, it removes the amd64 dev
# package and breaks every 64-bit link; install the runtime lib and add the
# development symlinks instead.
RUN apt-get update -qq \
  && apt-get install -y -qq --no-install-recommends \
    libunwind8:i386 \
    linux-libc-dev:i386 \
    zlib1g-dev:i386 \
  && for l in libunwind libunwind-x86; do \
       so=$(ls /usr/lib/i386-linux-gnu/$l.so.* 2>/dev/null | head -1); \
       [ -n "$so" ] && ln -sf "$(basename "$so")" "/usr/lib/i386-linux-gnu/$l.so"; \
     done \
  && rm -rf /var/lib/apt/lists/*

# The vendored libc++ does not compile with Ubuntu 22.04's default GCC 11.
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-12 20 \
  && update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-12 20

RUN python3 -m pip install \
    coloredlogs \
    construct \
    cxxfilt \
    jinja2 \
    kconfiglib \
    lark \
    pexpect==4.8.0 \
    pyelftools \
    pyserial==3.5 \
    pytest==6.2.5 \
    pytest-json==0.4.0 \
    pytest-ordering==0.6 \
    pytest-repeat==0.9.1 \
    stringcase

RUN python3 -m venv /opt/ntfc-venv \
  && /opt/ntfc-venv/bin/pip install \
    ntfc==0.0.1 \
    pytest==7.4.4 \
  && ln -s /opt/ntfc-venv/bin/ntfc /usr/local/bin/ntfc

RUN curl -fsSL https://storage.googleapis.com/git-repo-downloads/repo \
      -o /usr/local/bin/repo \
  && chmod +x /usr/local/bin/repo

COPY scripts/openvela-* /usr/local/bin/

RUN chmod a+x /usr/local/bin/openvela-*

RUN groupadd --gid "${OPENVELA_GID}" openvela \
  && useradd --uid "${OPENVELA_UID}" --gid "${OPENVELA_GID}" \
    --create-home --shell /bin/bash openvela \
  && mkdir -p /workspace \
  && chown openvela:openvela /workspace \
  && echo "openvela ALL=(ALL) NOPASSWD:ALL" >/etc/sudoers.d/openvela \
  && chmod 0440 /etc/sudoers.d/openvela

WORKDIR /workspace

USER openvela

CMD ["/bin/bash"]
