FROM ubuntu:16.04

RUN .github/workflows/ubuntu-setup-python.sh
RUN ldconfig /usr/local/lib

RUN python3.7 -m venv venv
# Upgrade pip
venv/bin/python3.7 -m pip install --upgrade pip
# Install dependencies
venv/bin/python3.7 -m pip install pyinstaller setuptools
venv/bin/python3.7 -m pip install -r requirements.txt
