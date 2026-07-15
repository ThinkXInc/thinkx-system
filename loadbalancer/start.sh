#!/bin/bash

# Starts the nginx service

start_service() {
    sudo systemctl start nginx.service
}

check_service_status() {
    echo "Checking the status of nginx service..."
    systemctl status nginx.service
}

start_service
check_service_status
