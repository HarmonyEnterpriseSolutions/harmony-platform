#!/bin/sh
#
# Copyright 2002-2003 Free Software Foundation
#
# This file is part of GNU Enterprise.
#
# GNU Enterprise is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2, or (at your option) any later version.
#
# GNU Enterprise is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with program; see the file COPYING. If not,
# write to the Free Software Foundation, Inc., 59 Temple Place
# - Suite 330, Boston, MA 02111-1307, USA.
#
# FILE:
# gnue-diag.sh
#
# DESCRIPTION:
# Technical support/system diagnostics script for POSIX systems.
#
# SYNTAX:
#
#  gnue-diag.sh [python-exe-to-test | system | config]
#
#  If run with no arguments, gnue-diag checks all
#  pythons found in $PATH
#
# Examples:
#
#  To show as much diag information as possible, including
#  every installed python, run: (this may be a long output)
#
#      ./gnue-diag.sh
#
#
#  To show information only about the installed  pythons, run:
#
#      ./gnue-diag.sh pycheck
#
#
#  To show information only about the system (not Python
#  information), run:
#
#      ./gnue-diag.sh system
#
#
#  To show information about the site-specific GNUe
#  configuration, run:  (this may be a long output)
#
#      ./gnue-diag.sh config
#
#
#  To show information on a specific Python (e.g., python2), run:
#
#      ./gnue-diag.sh python2
#


echo "GNU Enterprise"
echo "POSIX Diagnostics Script"
echo

checkConfig="N"
checkSystem="N"
checkPython="N"

grabAllPythons="N"

if [ "$1" = "system" ]
then
  checkSystem="Y"

elif [ "$1" = "config" ]
then
  checkConfig="Y"

elif [ "$1" = "pycheck" ]
then
  checkPython="Y"
  grabAllPythons="Y"

elif [ "$1z" != "z" ]
then
  PYTHONBINS=$1
  if [ `((echo print \'_Good_\'|$1) 2>&1)|grep -c _Good_` = "0" ]
  then
    echo "Cannot run $1"
    exit
  fi
  checkPython="Y"

else

  # Find all python binaries in the path

  checkConfig="Y"
  checkSystem="Y"
  checkPython="Y"
  grabAllPythons="Y"

fi

if [ "$grabAllPythons" = "Y" ]
then
  for f in `echo $PATH|awk '{gsub(":"," "); print $0}'`
  do

    if [ -e $f/python ]
    then
      PYTHONBINS="$PYTHONBINS `ls $f/python`"
    fi

    if [ -e $f/python? ]
    then
      PYTHONBINS="$PYTHONBINS `ls $f/python?`"
    fi

    if [ -e $f/python?.? ]
    then
      PYTHONBINS="$PYTHONBINS `ls $f/python?.?`"
    fi

  done
fi


if [ "$checkPython" = "Y" ]
then

  for python in $PYTHONBINS
  do
    echo "--------------------------------------------------------------------"
    echo "Python results for '$python'"
    echo
    echo '

# Perform python checking
import sys, string
print "Version:    %s" % string.replace(sys.version,"\n","\n            ")
print "Platform:   %s" % sys.platform
print "sys.path:   %s" % string.join(sys.path[1:],"\n            ")
print "Python XML module:      ",

try:
  from xml.sax import saxutils
  print "Installed"
except ImportError:
  print "**Not Installed**"

print "mxDateTime: ",

try:
  import DateTime
  print DateTime.__version__
except ImportError:
  try:
    from mx import DateTime
    print DateTime.__version__
  except ImportError:
    print "**Not Installed**"
except AttributeError:
  print "Installed"

sys.exit()

    ' | $python

    echo

    pybase=`
    echo "
import sys
print '%s/lib/python%s' % (sys.prefix, sys.version[:3])
sys.exit()
    "|$python`

    # Check any packages that might segfault them here...
    echo "Checking $pybase/site-packages:"
    for tst in wxPython pygresql psycopg pyPgSQL MySQLdb
    do
      if [ -e $pybase/site-packages/$tst* ]
      then
        echo "  $pybase/site-packages/$tst:  found"
      else
        echo "  $pybase/site-packages/$tst:  *NOT found*"
      fi
    done

  done
fi


if [ "$checkSystem" = "Y" ]
then
  echo "--------------------------------------------------------------------"
  echo "Generic System Information: "
  echo
  echo "ps -e | grep postmaster:"
  ps -e|grep postmaster
  echo
  echo "ps -e | grep mysql:"
  ps -e|grep mysql
fi

if [ "$checkConfig" = "Y" ]
then

  # TODO: This makes some hellacious assumptions

  echo "--------------------------------------------------------------------"
  echo "GNUe Configuration Information: "
  echo
  echo "Contents of /usr/local/gnue/etc:"
  if [ ! -e "/usr/local/gnue/etc" ]
  then
    echo "  Directory does not exist! Checking aborted"
  else
    ls /usr/local/gnue/etc
    echo
    echo "Contents of gnue.conf:"
    cat /usr/local/gnue/etc/gnue.conf
    echo
    echo "Contents of connections.conf"
    cat /usr/local/gnue/etc/connections.conf
    echo
    echo "Shebang line for /usr/local/bin/gnue-forms:"
    head -n1 /usr/local/bin/gnue-forms
  fi

fi

echo
