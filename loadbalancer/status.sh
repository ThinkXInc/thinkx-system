#!/bin/bash

# Displays the status of nginx service using different methods

echo "Using systemctl to check nginx status:"
sudo systemctl status nginx

echo "Listing all units related to nginx:"
systemctl list-units --type=service | grep nginx

echo "Checking nginx processes:"
ps aux | grep nginx | grep -v grep

echo "Displaying the last 3000 log lines for nginx:"
journalctl -u nginx.service --no-pager | tail -n 3000
