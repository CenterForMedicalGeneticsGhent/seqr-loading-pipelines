#!/usr/bin/env bash

CLUSTER=dataproc-cluster-no-vep

# create cluster
gcloud dataproc clusters create $CLUSTER   \
    --zone us-central1-b  \
    --master-machine-type n1-standard-4  \
    --master-boot-disk-size 100  \
    --num-workers 2  \
    --worker-machine-type n1-standard-4  \
    --worker-boot-disk-size 75 \
    --num-worker-local-ssds 1 \
    --image-version 1.1 \
    --properties "spark:spark.driver.extraJavaOptions=-Xss4M,spark:spark.executor.extraJavaOptions=-Xss4M,spark:spark.driver.memory=45g,spark:spark.driver.maxResultSize=30g,spark:spark.task.maxFailures=20,spark:spark.yarn.executor.memoryOverhead=30,spark:spark.kryoserializer.buffer.max=1g,hdfs:dfs.replication=1"  \
    --initialization-actions gs://hail-common/hail-init.sh,gs://gnomad-bw2/hail-jar/init-notebook.py
    #--project exac-gnomad \
    #--num-preemptible-workers 4 \

# open ipython notebook
python connect_cluster.py  --name $CLUSTER --port 8088

open http://localhost:8088  # open spark dashboard

