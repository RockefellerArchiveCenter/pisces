#!/bin/bash

TARGET=/etc/profile.d/pisces.sh

cp /data/app/zodiac/pisces/env.txt $TARGET

sed -i -e 's\PISCES_\export PISCES_\g' $TARGET
