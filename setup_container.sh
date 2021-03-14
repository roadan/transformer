#!/bin/bash

while getopts n:s:l:r:k:o:i: flag
do
    case "${flag}" in
        n) name=${OPTARG};;
        s) storagename=${OPTARG};;    #blacktransformer2
        l) location=${OPTARG};;       #australiaeast
        r) resourcegroup=${OPTARG};;  #blacktransformer2
        o) badookoutstore=${OPTARG};; 
        i) incontainer=${OPTARG};; 
    esac
done

echo "name: $name";
echo "storagename: $storagename";
echo "location: $location";
echo "resourcegroup: $resourcegroup";
echo "out container: $badookoutstore";
echo "in container: $incontainer";

connectionString=$(az storage account show-connection-string --resource-group $resourcegroup --name $storagename --query connectionString --output tsv)

az functionapp plan create \
  --resource-group $resourcegroup \
  --name badook-func \
  --location $location \
  --number-of-workers 1 \
  --sku EP3 \
  --is-linux

az functionapp create \
  --name $name \
  --storage-account $storagename \
  --plan badook-func \
  --resource-group $resourcegroup \
  --os-type Linux \
  --runtime python \
  --runtime-version 3.7 \
  --functions-version 3 \
  --deployment-container-image-name gcr.io/badook-cloud-public/blacktransformer:latest 

az functionapp config appsettings set \
  -n $name \
  -g $resourcegroup \
  --settings "AzureWebJobsStorage=$connectionString"

az functionapp config appsettings set \
  -n $name \
  -g $resourcegroup \
  --settings "badookinstore=$connectionString"

az functionapp config appsettings set \
  -n $name \
  -g $resourcegroup \
  --settings "badookoutstore=$badookoutstore"

az functionapp config appsettings set \
  -n $name \
  -g $resourcegroup \
  --settings "incontainer=$incontainer"
  
az functionapp config appsettings set --name $name \
  --resource-group $resourcegroup \
  --settings SCALE_CONTROLLER_LOGGING_ENABLED=AppInsights:Verbose