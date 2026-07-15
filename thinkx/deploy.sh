#!/bin/bash -e
#
# deploy.sh
#
# deploy corporate server
#
# usage:
# ./deploy.sh
#

ansible-playbook -i playbooks/thinkx playbooks/thinkx.yml
