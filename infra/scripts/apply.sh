#!/usr/bin/env bash
# supercom インフラを作成する。
#   ./scripts/apply.sh [staging|prod]   (既定 staging)
 
ENV="${1:-staging}"
cd "$(dirname "${BASH_SOURCE[0]:-$0}")/../terraform"
 
terraform apply -var="env=$ENV"
terraform output
 