#!/bin/bash
set -e

ZIP_DIR=$1
ZIP_NAME=$2

# remove unnecessary files
rm -rf fixtures \
  .git \
  .github \
  .coverage \
  .flake8 \
  .gitignore \
  .pre-commit-config.yaml \
  Dockerfile \
  entrypoint.sh \
  pisces-services.png \
  wait-for-it.sh
find . -type d -name __pycache__ -exec rm -r {} \+

# create zip file
zip -r $ZIP_NAME . -x "cc-test-reporter"
mkdir -p $ZIP_DIR
mv pisces.zip $ZIP_DIR/$ZIP_NAME