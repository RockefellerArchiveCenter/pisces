#!/bin/bash
set -e

# substitute env variables in config.py
envsubst < "pisces/config.py.deploy" > "pisces/config.py"

# substitute env variables in install_dependencies.sh
sed -i -e "s/\${ROOT_DIR}/$ROOT_DIR/g" deploy_scripts/install_dependencies.sh
sed -i -e "s/\${PYTHON_PATH}/$PYTHON_PATH/g" deploy_scripts/install_dependencies.sh

# substitute env variables in run_management_commands.sh
sed -i -e "s/\${ROOT_DIR}/$ROOT_DIR/g" deploy_scripts/run_management_commands.sh

# substitute env variables in validate_service.sh
sed -i -e "s/\${PISCES_PORT}/$PISCES_PORT/g" deploy_scripts/validate_service.sh
