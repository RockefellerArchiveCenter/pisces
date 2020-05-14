#!/bin/bash
set -e

# stop all running cron jobs
sudo killall crond

# stop cron
sudo systemctl stop crond
