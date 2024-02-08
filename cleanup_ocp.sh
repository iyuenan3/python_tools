#!/bin/bash
if [ "$#" -ne 1 ]; then
    echo "Warning: illegal number of parameters."
    echo "Usage: ${FUNCNAME[0]} <OCP ENV>"
    exit 1
fi
OCP_ENV=$1
SCRIPT_PATH=$(cd "$(dirname "$0")"; pwd)
OCP_CONFIG_FILE=$SCRIPT_PATH/aic-dep/sct/variables/$OCP_ENV/*.py
FILE_NUMBER=$(ls $OCP_CONFIG_FILE 2> /dev/null | wc -l)
if [ $FILE_NUMBER -eq 0 ]; then
    echo "$OCP_CONFIG_FILE does not exist"
    exit 1
fi
NAMESPACE=$(cat $OCP_CONFIG_FILE | grep -E ^DEPLOYER_NAMESPACE | awk '{print $3}' | sed $'s/\'//g' | tr -d '\r\n')
if [ ! $NAMESPACE ]; then
    echo "NAMESPACE is NULL"
    exit 1
fi
CTRL_IP=$(cat $OCP_CONFIG_FILE | grep -E ^DEPLOYER_CONTROLLER_IP | awk '{print $3}' | sed $'s/\'//g' | tr -d '\r\n')
if [ ! $CTRL_IP ]; then
    echo "CTRL_IP is NULL"
    exit 1
fi
CORE_USER=core
CORE_PASSWD=system123
SSH_OPT="sshpass -p $CORE_PASSWD ssh -o StrictHostKeyChecking=no -o LogLevel=ERROR $CORE_USER@"

# UPDATE REMOTE HOST IDENTIFICATION
ssh-keygen -f "~/.ssh/known_hosts" -R "$CTRL_IP"

# clear OCP registry and local image files
prune_image_cmd="oc adm prune images --keep-younger-than=1440m --prune-registry=true --num-workers=5 --keep-tag-revisions=0 --all=true --force-insecure=true --confirm"
echo "[$CORE_USER@$CTRL_IP]:~$ $prune_image_cmd"
$SSH_OPT$CTRL_IP $prune_image_cmd
sleep 5
for node_ip in $($SSH_OPT$CTRL_IP "kubectl get node -o wide | grep -w Ready | awk '{print \$6}'")
    do
    echo "[$CORE_USER@$node_ip]:~$ podman image ls | grep $NAMESPACE | awk '{print \$3}' | xargs podman image rm"
    $SSH_OPT$CTRL_IP "sudo podman image ls | grep $NAMESPACE | awk '{print \$3}' | xargs sudo podman image rm"
    sleep 5
    $SSH_OPT$CTRL_IP "podman image ls | grep $NAMESPACE | awk '{print \$3}' | xargs podman image rm"
    sleep 5
    done

