#!/bin/bash

if [ `hostname` == "api.bauble.io" ] ; then
    echo "NOT ON api.bauble.io YOU FOOL!"
    exit 1
fi

sudo -u postgres psql -c 'drop database bauble;'
if [ $? == 1 ] ; then exit ; fi

sudo -u postgres psql -c 'create database bauble;'
if [ $? == 1 ] ; then exit ; fi
read -p "Press a key when the server is started..."
PYTHONPATH=. bin/initdb.py
PYTHONPATH=. bin/set_admin_password.py test
PYTHONPATH=. bin/create_test_org.py



