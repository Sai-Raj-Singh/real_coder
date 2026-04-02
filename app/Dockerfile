###############################################
# BASE IMAGE
###############################################
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

###############################################
# SYSTEM DEPENDENCIES
###############################################
RUN apt-get update && apt-get install -y \
    git \
    python3 \
    python3-pip \
    python3-setuptools \
    python-is-python3 \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*
 
###############################################
# GO 1.22
###############################################
RUN wget -q https://go.dev/dl/go1.22.12.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go1.22.12.linux-amd64.tar.gz \
    && rm go1.22.12.linux-amd64.tar.gz
 
ENV PATH="/usr/local/go/bin:${PATH}"
 
###############################################
# PYTHON TEST DEPENDENCIES
###############################################
RUN pip3 install --no-cache-dir \
    pytest==8.3.5 \
    requests==2.32.3
 
###############################################
# WORKING DIRECTORY + GIT SETUP
###############################################

WORKDIR /app

RUN git init \
    && git config --global user.email "agent@example.com" \
    && git config --global user.name "Agent" \
    && echo "# Workspace" > README.md \
    && git add README.md \
    && git commit -m "Initial commit"

###############################################
# EVALUATION ASSETS DIRECTORY
###############################################
# Populated at RUNTIME by the evaluation script.
RUN mkdir -p /eval_assets

CMD ["/bin/bash"]