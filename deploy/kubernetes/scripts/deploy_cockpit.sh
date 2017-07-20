#!/usr/bin/env bash

SCRIPT_DIR="$( cd "$(dirname "$0")" ; pwd -P )"
source ${SCRIPT_DIR}/init_env.sh
set -x

# http://cockpit-project.org/guide/latest/feature-kubernetes.html

if [ "$DELETE_BEFORE_DEPLOY" ]; then
    kubectl delete -f kubernetes/settings/cockpit/cockpit.yaml
fi

if [ "$DEPLOY_TO_PREFIX" = 'local' ]; then
    # disable username/password prompt - https://github.com/cockpit-project/cockpit/pull/6921
    kubectl create clusterrolebinding anon-cluster-admin-binding --clusterrole=cluster-admin --user=system:anonymous
fi

kubectl apply -f kubernetes/settings/cockpit/cockpit.yaml

# print username, password for logging into cockpit
kubectl config view
wait_until_pod_is_running cockpit
