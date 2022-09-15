FROM ubuntu:16.04

WORKDIR /usr/src/retype
COPY . .

RUN chmod 777 .github/workflows/ubuntu-setup-python.sh
RUN .github/workflows/ubuntu-setup-python.sh
RUN ldconfig /usr/local/lib

RUN python3.7 -m venv venv
# Upgrade pip
RUN venv/bin/python3.7 -m pip install --upgrade pip
# Install dependencies
RUN venv/bin/python3.7 -m pip install pyinstaller setuptools
RUN venv/bin/python3.7 -m pip install -r requirements.txt
