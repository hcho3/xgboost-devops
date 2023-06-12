#!/bin/bash

set -euo pipefail

manager_id=$(python -m awscli ec2 describe-instances \
  --filters Name=tag:Name,Values='XGBoost CI Dashboard' \
  --query 'Reservations[*].Instances[*].{Instance:InstanceId}' \
  --output text --region us-west-2)
manager_az=$(python -m awscli ec2 describe-instances \
  --filters Name=tag:Name,Values='XGBoost CI Dashboard' \
  --query 'Reservations[*].Instances[*].{AZ:Placement.AvailabilityZone}' \
  --output text --region us-west-2)

ssh-keygen -t rsa -f my_rsa_key -b 4096 -q -N "" <<<y
pubkey=$(cat my_rsa_key.pub)
python -m awscli ec2-instance-connect send-ssh-public-key --instance-id $manager_id \
  --availability-zone $manager_az --instance-os-user ubuntu --ssh-public-key "$pubkey" \
  --region us-west-2
rsync -PaLv -e "ssh -i ./my_rsa_key -o StrictHostKeyChecking=no" ./dashboard/ \
  ubuntu@xgboost-ci.net:/var/www/xgboost-ci.net/html/dashboard
