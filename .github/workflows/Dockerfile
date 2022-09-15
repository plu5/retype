FROM ubuntu:16.04

RUN ls -A

RUN .github/workflows/ubuntu-setup-python.sh
RUN ldconfig /usr/local/lib

RUN python3.7 -m venv venv
# Upgrade pip
RUN venv/bin/python3.7 -m pip install --upgrade pip
# Install dependencies
RUN venv/bin/python3.7 -m pip install pyinstaller setuptools
RUN venv/bin/python3.7 -m pip install -r requirements.txt
