#!/bin/bash

# stop all running cron jobs
sudo pkill crond

# stop cron
sudo systemctl stop crond
