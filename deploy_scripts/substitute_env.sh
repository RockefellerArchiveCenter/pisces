#!/bin/bash
set -e

# substitute env variables in config.py
envsubst < "pisces/config.py.deploy" > "pisces/config.py"

# substitute env variables in install_dependencies.sh
envsubst < "deploy_scripts/install_dependencies.sh.deploy" > "deploy_scripts/install_dependencies.sh"

# substitute env variables in run_management_commands.sh
envsubst < "deploy_scripts/run_management_commands.sh.deploy" > "deploy_scripts/run_management_commands.sh"

# substitute env variables in validate_service.sh
envsubst < "deploy_scripts/validate_service.sh.deploy" > "deploy_scripts/validate_service.sh"
