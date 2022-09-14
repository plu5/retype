#!/bin/bash -e
# pyinstaller-hack.sh: apply or unapply sys._MEIPASS hack to PyInstaller
# When applied, the built executable will search for supporting files in
#  ./include instead of .
# Takes argument 'apply' or 'unapply'.

THE_LINE='sys._MEIPASS = os.path.join(sys._MEIPASS, "include")'
ARG=$1  # should be 'apply' or 'unapply'

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

cd venv/lib/python3.7/site-packages/PyInstaller/loader

if [[ $ARG == 'apply' ]]; then
    add_line
elif [[ $ARG == 'unapply' ]]; then
    rem_line
else
    echo "argument error"
fi
