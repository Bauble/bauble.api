#!/bin/bash

echo "\
####################
# 
# THIS WILL DESTROY THE CURRENT DATABASE
#
####################"

read -p "Are you sure you want to do this? " -n1 CONFIRM
echo
if [[ $CONFIRM != "y" && $CONFIRM != "Y" ]] ; then
    exit 1
fi

read -p "*** Are you sure you're sure? " -n1 CONFIRM
echo
if [[ $CONFIRM != "y" && $CONFIRM != "Y" ]] ; then
    exit 1
fi

if [[ $OPENSHIFT_NAMESPACE == "baubleio" ]] ; then
    PSQL="psql"
    SUDO=""
elif [[ `uname` == "Darwin" ]]  ; then
    PSQL="/Applications/Postgres93.app/Contents/MacOS/bin/psql"
    SUDO=""
else
    PSQL="psql"
    SUDO="sudo -u postgres"
fi

DB_NAME='bauble'
CREATE_ROLE="false"

if [[ $OPENSHIFT_POSTGRESQL_DB_USERNAME != "" ]] ; then
    DB_OWNER=$OPENSHIFT_POSTGRESQL_DB_USERNAME
else
    DB_OWNER="test"
    CREATE_ROLE="true"
fi

$SUDO $PSQL -c 'drop database if exists $DB_NAME;'
if [ $? == 1 ] ; then exit ; fi

if [[ $CREATE_ROLE == "true" ]] ; then
    $SUDO $PSQL -c "drop role if exists $DB_OWNER;"
    if [ $? == 1 ] ; then exit ; fi

    $SUDO $PSQL -c "create role $DB_OWNER with createdb createrole login password '$DB_OWNER';"
    #$SUDO $PSQL -c "create role $DB_OWNER with createdb createrole login password 'test';"
    if [ $? == 1 ] ; then exit ; fi
fi

$SUDO $PSQL -c "create database $DB_NAME with owner=$DB_OWNER;"
if [ $? == 1 ] ; then exit ; fi

read -p "Start the Bauble API server and press a key when it's ready..."
PYTHONPATH=. bin/initdb.py

read -s -p "admin password: " PASSWORD
PYTHONPATH=. bin/set_admin_password.py $PASSWORD

