#!/bin/bash

echo Running `basename "$0"`

# start apache
sudo systemctl restart httpd
