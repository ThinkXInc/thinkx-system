set -eu -o pipefail
if [ $1 = "api" ] || [ $1 = "batch" ]; then
    echo "Deploy for $1"
else
    echo $1
    echo "[Error]: The required value is not set."
    $(exit 1)
fi

cd `dirname $0`

echo "Building citywalk-${1} instance is started."

INSTANCE_ID=`aws ec2 run-instances --region ap-northeast-1 \
  --image-id ami-0ef85cf6e604e5650 --count 1 \
  --instance-type t3.medium --key-name citywalk \
  --subnet-id subnet-0ab485d3a707e4581 \
  --security-group-ids sg-0f96c4e071b5e9d61 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=citywalk-master}]' \
  --credit-specification CpuCredits=standard \
  --associate-public-ip-address \
  --iam-instance-profile Name=CITYWALK-ApplicationServers \
  | jq -r '.Instances[0].InstanceId' `

for ((i=0; i<5; i++)); do
    INSTANCE_STATUS=`aws ec2 describe-instances --instance-ids ${INSTANCE_ID} | jq -r '.Reservations[0].Instances[0].State.Name'`
    if [ $INSTANCE_STATUS = "running" ]; then
        echo "Instance started."
        break
    elif [ $INSTANCE_STATUS = "pending" ]; then
        echo "Instance is pendding."
        sleep 5s
    else
        echo "[Error]: Create Instance Error: ${INSTANCE_STATUS}"
        $(exit 1)
    fi
done

MASTER_INSTANCE_IP=`aws ec2 describe-instances --instance-ids ${INSTANCE_ID} \
    | jq -r '.Reservations[0].Instances[0].PublicIpAddress' `

cat <<EOF > ~/.ssh/aws.config
Host citywalk-${1}
    HostName $MASTER_INSTANCE_IP
    IdentityFile ~/.ssh/citywalk.pem
    StrictHostKeyChecking no
    user ubuntu
    Port 22
    TCPKeepAlive yes
    IdentitiesOnly yes
EOF

sleep 10s

set +e
for ((i=0; i<5; i++)); do
    ansible-playbook -i playbooks/$1 playbooks/$1.yml
    if [ $? = 0 ]; then
        echo "Ansible succeeded."
        break
    else
        echo "[Error]: Excute Ansible Error"
        if [ $i = 4 ]; then
        set -e
        $(exit 1)
        fi
        sleep 5s
    fi
done

set -eu -o pipefail

if [ $2 = "production" ] || [ $2 = "staging" ]; then

    echo "Building Image is started."
    AMI_NAME="citywalk-${1}-${2}-$(date "+%Y%m%d-%H%M%S")"

    IMAGE_ID=`aws ec2 create-image \
        --instance-id ${INSTANCE_ID} \
        --name ${AMI_NAME} \
        --description "An AMI for citywalk-${1} server" \
        | jq -r '.ImageId' `

    for ((i=0; i<30; i++)); do
    IMAGE_STATUS=`aws ec2 describe-images --image-ids ${IMAGE_ID} | jq -r '.Images[0].State'`
    if [ $IMAGE_STATUS = "available" ]; then
        echo "Image is available."
        break
    elif [ $IMAGE_STATUS = "pending" ]; then
        echo "Now Building"
        sleep 60s
    else
        echo "[Error]: Create AMI Error: ${IMAGE_STATUS}"
        $(exit 1)
    fi
    done


    AUTOSCALING_CONFIG_NAME="citywalk-${1}-${2}-$(date "+%Y%m%d-%H%M%S")"

    aws ec2 describe-images --image-ids ${IMAGE_ID} | jq -r '.Images[0].BlockDeviceMappings[0]'

    SNAPSHOT_ID=`aws ec2 describe-images --image-ids ${IMAGE_ID} | jq -r '.Images[0].BlockDeviceMappings[0].Ebs.SnapshotId'`

    echo "Update Autoscaling."

    AUTOSCALING_GROUP_NAME="citywalk-${1}-${2}"

    INSTANCE_TYPE="t2.micro"
    if [ $1 = "api" ] && [ $2 = "production" ]; then
        AUTOSCALING_GROUP_NAME="citywalk-ag"
        INSTANCE_TYPE="t2.micro"
    elif [ $1 = "batch" ] && [ $2 = "production" ]; then
        AUTOSCALING_GROUP_NAME="citywalk-history-consumer"
    fi

    aws autoscaling create-launch-configuration --launch-configuration-name ${AUTOSCALING_CONFIG_NAME} \
    --image-id ${IMAGE_ID} --instance-type ${INSTANCE_TYPE} --security-groups sg-045835b9f270b3b79 \
    --iam-instance-profile CITYWALK-ApplicationServers \
    --block-device-mappings "[{\"DeviceName\":\"/dev/sda1\",\"Ebs\":{\"SnapshotId\":\"${SNAPSHOT_ID}\"}}]"

    aws autoscaling update-auto-scaling-group --auto-scaling-group-name ${AUTOSCALING_GROUP_NAME} \
    --launch-configuration-name ${AUTOSCALING_CONFIG_NAME} --min-size 2 --max-size 2

    echo "Reflesh Instance."

    aws autoscaling start-instance-refresh --auto-scaling-group-name ${AUTOSCALING_GROUP_NAME}

    for ((i=0; i<30; i++)); do
        REFLESH_STATUS=`aws autoscaling describe-instance-refreshes --auto-scaling-group-name ${AUTOSCALING_GROUP_NAME} | jq -r '.InstanceRefreshes[0].Status'`
        if [ $REFLESH_STATUS = "Successful" ]; then
            echo "Instance Reflesh is Successful."
            break
        elif [ $REFLESH_STATUS = "InProgress" ] || [ $REFLESH_STATUS = "Pending" ]; then
            echo "Now Refleshing"
            sleep 60s
        else
            echo "[Error]: Reflesh Instance Error: ${REFLESH_STATUS}"
            $(exit 1)
        fi
    done

    aws ec2 terminate-instances --instance-ids ${INSTANCE_ID}

    echo "${2} deploy is succeeded."
else
    echo "Development deploy is succeeded."
fi
