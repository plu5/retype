#!/bin/bash -e
# pyinstaller-hack.sh: apply or unapply sys._MEIPASS hack to PyInstaller
# When applied, the built executable will search for supporting files in
#  ./include instead of .
# POSITIONAL ARGUMENTS:
# 1: 'apply' or 'unapply'
# 2: Path to site-packages

THE_LINE='sys._MEIPASS = os.path.join(sys._MEIPASS, "include")'
ARG=$1  # should be 'apply' or 'unapply'
SITE_PACKAGES=$2

function add_line()
{
  MEIPASS_LINENUM=$(cat pyimod02_importers.py | sed -n '/sys._MEIPASS/{=;q;}')
  sed -i "${MEIPASS_LINENUM}i ${THE_LINE}" pyimod02_importers.py
}

function rem_line()
{
  LINE_TO_REM='sys._MEIPASS = os.path.join(sys._MEIPASS, "include")'
  sed -i "/${LINE_TO_REM}/d" pyimod02_importers.py
}

cd ${SITE_PACKAGES}/PyInstaller/loader

if [[ $ARG == 'apply' ]]; then
    add_line
elif [[ $ARG == 'unapply' ]]; then
    rem_line
else
    echo "argument error"
fi
