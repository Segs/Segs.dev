#!/bin/sh
# Set proper current working directory and start SEGS.
# For use with segs.service systemd unit file.
cd /opt/segs/Segs/bld/out
./segs_server
