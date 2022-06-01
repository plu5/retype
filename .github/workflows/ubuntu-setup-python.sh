#!/bin/bash -e

VERSION="3.7.4"

apt update && apt upgrade -y && apt clean && apt update
apt-get install -y wget build-essential checkinstall  libreadline-gplv2-dev  libncursesw5-dev  libssl-dev  libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev

cd /usr/src
wget https://www.python.org/ftp/python/${VERSION}/Python-${VERSION}.tgz
tar xzf Python-${VERSION}.tgz
cd Python-${VERSION}

./configure --enable-optimizations --enable-shared
make altinstall

ldconfig /usr/local/lib
