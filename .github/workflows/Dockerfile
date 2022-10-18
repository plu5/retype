FROM ubuntu:16.04

ARG PYTHON_VERSION=3.7.4

# Install dependencies for building Python
RUN apt update && apt upgrade -y && apt clean && apt update
RUN apt-get install -y wget build-essential checkinstall \
libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev \
libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev

# Build Python
WORKDIR /usr/src
RUN wget https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz
RUN tar xzf Python-${PYTHON_VERSION}.tgz
WORKDIR Python-${PYTHON_VERSION}
RUN ./configure --enable-optimizations --enable-shared
RUN make altinstall

# Run ldconfig (Python is unable to find its shared libraries otherwise)
RUN ldconfig /usr/local/lib

# Set up venv and install retype requirements
WORKDIR /usr/src/app
RUN python3.7 -m venv venv
RUN venv/bin/python3.7 -m pip install --upgrade pip
RUN venv/bin/python3.7 -m pip install pyinstaller setuptools
COPY requirements.txt .
RUN venv/bin/python3.7 -m pip install -r requirements.txt
