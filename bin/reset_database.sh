#!/bin/bash

if [ `hostname` == "api.bauble.io" ] ; then
    echo "NOT ON api.bauble.io YOU FOOL!"
    exit 1
fi

PSQL="psql"
SUDO="sudo -u postgres"
if [[ `uname` == "Darwin" ]] ; then
    PSQL="/Applications/Postgres93.app/Contents/MacOS/bin/psql"
    SUDO=""
fi

$SUDO $PSQL -c 'drop database if exists bauble;'
if [ $? == 1 ] ; then exit ; fi

$SUDO $PSQL -c 'drop role if exists test;'
if [ $? == 1 ] ; then exit ; fi

$SUDO $PSQL -c 'create role test with createdb createrole login;'
if [ $? == 1 ] ; then exit ; fi

$SUDO $PSQL -c 'create database bauble with owner=test;'
if [ $? == 1 ] ; then exit ; fi
read -p "Start the Bauble API server and press a key when it's ready..."
PYTHONPATH=. bin/initdb.py
PYTHONPATH=. bin/set_admin_password.py test
PYTHONPATH=. bin/create_test_org.py



