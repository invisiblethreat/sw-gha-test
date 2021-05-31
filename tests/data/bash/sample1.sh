#!/bin/bash
set -e

#################
### Do checks ###
#################
if [ -z "$CUSTOM_TAG" ] || [ -z "$SERVICE" ] || [ -z "$CLUSTER_KEY" ] ; then
    echo "Error: Make sure you are providing all necessary env vars to run.sh!"
    exit 1
fi

####################
### Get env vars ###
####################
export PUSH_IMAGES="no"
export TEMPLATE_ONLY=${TEMPLATE_ONLY:-"no"}
export CLUSTER_KEY=${CLUSTER_KEY:-""}
export URI_NAMESPACE=${URI_NAMESPACE:-"gcr.io/company-product-dev"}
export PRODUCT_FLAVOR=Pro
service_str=$(echo $SERVICE | tr a-z A-Z | tr '-' '_')
export PRODUCT_${service_str}_TAG="$CUSTOM_TAG"
export PYTHONPATH="./infra/jenkins/product-build-common"
export NAMESPACE=${NAMESPACE:-"product"}

if [ -n "$PRODUCT_COMMIT_HASH" ] ; then
    RELEASE="$PRODUCT_COMMIT_HASH"
else
    RELEASE="$CUSTOM_TAG"
fi

######################
### Clone k8s repo ###
######################
./kubernetes/clone.sh

##############################
### Build charts container ###
##############################
python ./infra/jenkins/build-images/build-push-charts-container.py

############################
### Run template/upgrade ###
############################
# TODO: NEED THE DEFAULT
RELEASE=${RELEASE} \
ACTION="template" \
ENV=${ENV:-"dev"} \
CLUSTER_KEY=${CLUSTER_KEY} \
NAMESPACE=${NAMESPACE} ./kubernetes/product-deploy/app-setup.sh

#####################################
### Apply the changes via kubectl ###
#####################################
if [ "$TEMPLATE_ONLY" = "no" ] ; then
    kubectl apply -f ./kubernetes/product-deploy/manifests/product/charts/$SERVICE/templates
fi
