FROM ubuntu:16.04

WORKDIR /usr/src/retype
RUN ls -A ; echo "@1"
COPY . .
RUN ls -A ; echo "@2"

RUN .github/workflows/ubuntu-setup-python.sh
RUN ldconfig /usr/local/lib

RUN python3.7 -m venv venv
# Upgrade pip
RUN venv/bin/python3.7 -m pip install --upgrade pip
# Install dependencies
RUN venv/bin/python3.7 -m pip install pyinstaller setuptools
RUN venv/bin/python3.7 -m pip install -r requirements.txt
