#!/bin/bash

echo Running `basename "$0"`

# get status endpoint
curl https://localhost:8007/status/ # TODO: port should be an environment variable
