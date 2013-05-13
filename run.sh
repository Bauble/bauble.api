#!/bin/bash
#while ! ./run.py local
while `true`
do
  sleep 1
  echo "Starting..."
  ./run.py local
  
done
