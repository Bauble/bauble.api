#!/bin/bash
#while ! ./run.py local
while `true`
do
  sleep 1
  echo "Starting..."
  foreman start  
done
