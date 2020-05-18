#!/bin/bash
set -e

for TEMPLATE in pisces/config.py.deploy \
  appspec.yml.deploy \
  deploy_scripts/*.deploy
do
  if [[ -f "$TEMPLATE" ]]; then
    echo "Replacing variables in $TEMPLATE"
    envsubst < "$TEMPLATE" > `echo "$TEMPLATE" | sed -e 's/\(\.deploy\)*$//g'`
    rm $TEMPLATE
  fi
done
