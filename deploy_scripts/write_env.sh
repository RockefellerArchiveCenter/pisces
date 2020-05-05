#!/bin/bash

echo Running `basename "$0"`

rm env.txt

# Writes environment variables starting with $1 to env.txt, after replacing $1 with $2
echo "`printenv | grep $1`" | sed "s/${1}/${2}/g" >> env.txt
