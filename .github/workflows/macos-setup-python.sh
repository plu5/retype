#!/bin/bash -e

VERSION="3.7.4"

wget https://www.python.org/ftp/python/${VERSION}/python-${VERSION}-macosx10.9.pkg -P /tmp/
sudo installer -pkg /tmp/python-${VERSION}-macosx10.9.pkg -target /Applications
