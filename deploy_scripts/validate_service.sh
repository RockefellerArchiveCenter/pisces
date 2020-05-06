#!/bin/bash

echo Running `basename "$0"`

# get status endpoint
curl http://localhost:$PISCES_PORT/status/
