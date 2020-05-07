#!/bin/bash

rm env.txt

# Writes environment variables to env.txt
echo "`printenv | grep $1`" >> env.txt
