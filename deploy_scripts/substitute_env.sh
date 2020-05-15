#!/bin/bash
set -e

for TEMPLATE in pisces/config.py.deploy deploy_scripts/install_dependencies.sh.deploy \
deploy_scripts/run_management_commands.sh.deploy deploy_scripts/validate_service.sh.deploy
do
  envsubst < "$TEMPLATE" > echo "$TEMPLATE" | sed -e 's/\(\.deploy\)*$//g'
  rm $TEMPLATE
done
