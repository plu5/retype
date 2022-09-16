#!/bin/bash -e
# pyinstaller-hack.sh: apply or unapply sys._MEIPASS hack to PyInstaller
# When applied, the built executable will search for supporting files in
#  ./include instead of .
# POSITIONAL ARGUMENTS:
# 1: 'apply' or 'unapply'
# 2: Path to site-packages

ARG=$1  # should be 'apply' or 'unapply'
SITE_PACKAGES=$2

FILE="pyimod02_importers.py"
THE_LINE='sys._MEIPASS = os.path.join(sys._MEIPASS, "include")'

function add_line()
{
  MEIPASS_LINENUM=$(cat $FILE | sed -n '/sys._MEIPASS/{=;q;}')
  MEIPASS_LINENUM=$((MEIPASS_LINENUM + 1))
  printf '%s\n' $MEIPASS_LINENUM a "$THE_LINE" . wq | ed $FILE
}

function rem_line()
{
  printf '%s\n' "g/$THE_LINE/d" . wq | ed $FILE
}

cd ${SITE_PACKAGES}/PyInstaller/loader

if [[ $ARG == 'apply' ]]; then
    add_line
elif [[ $ARG == 'unapply' ]]; then
    rem_line
else
    echo "argument error"
fi
