#!/usr/bin/env bash

kubectl delete deployments --all
kubectl delete replicationcontrollers --all
kubectl delete services --all
kubectl delete pods --all

docker kill $(docker ps -q)
docker rmi -f $(docker images -q)

if [ "$DEPLOY_TO_PREFIX" = 'gcloud' ]; then
    gcloud container clusters delete $CLUSTER_NAME --zone $GCLOUD_ZONE --no-async
    gcloud compute disks delete ${DEPLOY_TO}-elasticsearch-disk --zone $GCLOUD_ZONE
fi
