#!/bin/bash

# Stops the nginx service

stop_service() {
    sudo systemctl stop nginx.service
}

check_service_status() {
    echo "Checking the status of nginx service..."
    systemctl status nginx.service
}

stop_service
check_service_status
