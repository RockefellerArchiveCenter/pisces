#!/bin/bash

echo Running `basename "$0"`

# get status endpoint
curl https://localhost:$PISCES_PORT/status/
