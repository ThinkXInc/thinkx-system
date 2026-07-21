#!/bin/bash -e
#
# deploy.sh
#
# usage:
#   ./deploy.sh production|staging|api|batch|ftp1
#

if [[ ! $HOSTNAME =~ ^bastion ]]; then
    echo '[WARN] Please execute this on bastion'
    #exit 1
fi

case "$1" in
production)  # *includes api, batch, ftp
    target=production
    ;;
staging)
    target=staging
    ;;
api)
    target=api
    ;;
web)
    target=web
    ;;
batch)
    target=batch
    ;;
ftp1)
    target=ftp1
    ;;
vpn1)
    target=vpn1
    ;;
maintenance_on)
    target=maintenance_on
    ;;
maintenance_off)
    target=maintenance_off
    ;;
#load_test)
#    target=load_test
#    ;;
#mongo_replica)
#    target=mongo_replica
#    ;;
*)
    echo "Please set deployment target environment. (production|staging|api|batch|ftp1|vpn1|maintenance_on|maintenance_off|)"
    exit 1
esac

if [ -n $target ]; then
    ansible-playbook -i playbooks/$target playbooks/$target.yml
fi
