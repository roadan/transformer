#!/bin/bash

while getopts n:s:l:r:k: flag
do
    case "${flag}" in
        n) name=${OPTARG};;
        s) storagename=${OPTARG};;    #blacktransformer2
        l) location=${OPTARG};;       #australiaeast
        r) resourcegroup=${OPTARG};;  #blacktransformer2
    esac
done

echo "name: $name";
echo "storagename: $storagename";
echo "location: $location";
echo "resourcegroup: $resourcegroup";

# az storage account create \
#   --name $storagename \
#   --location australiaeast \
#   --resource-group bdktransformers \s

#   --sku Standard_LRS

connectionString=$(az storage account show-connection-string --resource-group $resourcegroup --name $storagename --query connectionString --output tsv)

az functionapp plan create \
  --resource-group $resourcegroup \
  --name $name \
  --location $location \
  --number-of-workers 1 \
  --sku EP1 \
  --is-linux

az functionapp create \
  --name $name \
  --storage-account $storagename \
  --plan $name \
  --resource-group $resourcegroup \
  --os-type Linux \
  --runtime python \
  --runtime-version 3.7 \
  --functions-version 3 \
  --disable-app-insights \
  --deployment-container-image-name bdktransformers.azurecr.io/badook/blacktransformer:latest

az functionapp config appsettings set \
  -n $name \
  -g $resourcegroup \
  --settings "AzureWebJobsStorage=$connectionString"

az functionapp config appsettings set \
  -n $name \
  -g $resourcegroup \
  --settings "badookinstore=$connectionString"

# az storage share create --account-name $storagename --account-key $key --name sqlitefiles

# az storage directory create --account-name $storagename --account-key $key --share-name sqlitefiles --name incoming

# az webapp config storage-account add \
#   --resource-group $resourcegroup \
#   --name $name \
#   --custom-id tranformerId \
#   --storage-type AzureFiles \
#   --share-name sqlitefiles \
#   --account-name $storagename \
#   --mount-path /bdk \
#   --access-key XijJFcWz5m3o14HRr/D35zyuJYV6ozxpJZNOcJEq/b7lrDe8AcNfFzCzlM0Cdmhgi6v0ha1uaMHuF6Jioz7Vcw==