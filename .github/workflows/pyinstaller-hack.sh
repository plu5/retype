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
  if ! command -v ed &> /dev/null; then
    sed -i "${MEIPASS_LINENUM}i ${THE_LINE}" $FILE
  else
    printf '%s\n' $((MEIPASS_LINENUM - 1)) a "$THE_LINE" . wq | ed $FILE
  fi
}

function rem_line()
{
  if ! command -v ed &> /dev/null; then
    sed -i "/${THE_LINE}/d" $FILE
  else
    printf '%s\n' "g/$THE_LINE/d" . wq | ed $FILE
  fi
}

cd ${SITE_PACKAGES}/PyInstaller/loader

if [[ $ARG == 'apply' ]]; then
    add_line
elif [[ $ARG == 'unapply' ]]; then
    rem_line
else
    echo "argument error"
fi
