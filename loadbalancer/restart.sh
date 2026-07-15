#!/bin/bash

# Usage Examples:
# ./restart.sh                  - Restarts the nginx service
# ./restart.sh reload           - Reloads the nginx service

restart_service() {
    echo "Restarting nginx service..."
    sudo systemctl restart nginx.service
}

reload_service() {
    echo "Reloading nginx service..."
    sudo systemctl reload nginx.service
}

check_service_status() {
    echo "Checking the status of nginx service..."
    systemctl status nginx.service
}

check_nginx_config() {
    echo "Checking nginx configuration..."
    sudo nginx -t -c /src/loadbalancer/nginx.conf
    return $?  # Return the exit status of the nginx config test command
}

# First check if nginx configuration is valid
if check_nginx_config; then
    echo "Nginx configuration is valid."

    # Decide action based on argument
    if [ "$1" == "reload" ]; then
        reload_service
    else
        restart_service
    fi

    # Uncomment to check service status after operation
    # check_service_status
else
    echo "Nginx configuration test failed. Operation aborted to prevent service disruption."
fi
