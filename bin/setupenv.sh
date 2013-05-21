#!/bin/bash -i

PROJECT_NAME="bauble.api"

# make sure we have python3
if [[ `which python3` == "" ]] ; then
    echo "Python3 not installed."
    if [[ `uname` == "Darwin" ]] ;then 
        echo "Try: brew install python3 --with-brewed-openssl"
    fi
    exit 1
fi

# make sure we have pip for python3
if [[ `python3 -c "import pip" 2&>1 ; echo $?` == 1 ]] ; then
    echo "pip not installed for python 3."
    exit 1
fi

# create the virtualenv if it doesn't already exist
if [[ ! -d $WORKON_HOME/$PROJECT_NAME ]] ; then
    mkvirtualenv --distribute -p `which python3` $PROJECT_NAME
else
    echo $WORKON_HOME/$PROJECT_NAME already exists.
fi    

workon $PROJECT_NAME
python3 -c 'import pip ; pip.main(["install", "-r", "requirements.txt"])'

