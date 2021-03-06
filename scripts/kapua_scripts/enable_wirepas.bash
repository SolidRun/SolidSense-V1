#!/bin/bash
# script that is enabling Wirepas on a standard gateway
# assume to be executed from Kpaua in /tmp
# the SolidSense-conf-custom.yml file with Wirepas is assumed to be part of the zip file
#
# get the file from the server
curl -o SolidSense-conf-custom.yml https://images.solidsense.io/SolidSense/config/SolidSense-conf-wirepas.yml
cp -v SolidSense-conf-custom.yml /data/solidsense/config
ls -l /data/solidsense/config
# soft reconfig
rm -v /opt/eclipse/kura/user/snapshots/*
/opt/SolidSense/bin/restart
