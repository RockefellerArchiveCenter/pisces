#!/bin/bash
set -e

# get status endpoint
curl http://localhost:${PISCES_PORT}/status/
