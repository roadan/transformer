#!/bin/bash

while getopts n:s:l:r:k:o:i:v:x: flag

do
    case "${flag}" in
        n) name=${OPTARG};;
        s) storagename=${OPTARG};;    #blacktransformer2
        l) location=${OPTARG};;       #australiaeast
        r) resourcegroup=${OPTARG};;  #blacktransf  ormer2
        o) badookoutstore=${OPTARG};; 
        i) incontainer=${OPTARG};; 
        v) vnet=${OPTARG};;
        x) subnet=${OPTARG};;
    esac
done

echo "name: $name";
echo "storagename: $storagename";
echo "location: $location";
echo "resourcegroup: $resourcegroup";
echo "out container: $badookoutstore";
echo "in container: $incontainer";

connectionString=$(az storage account show-connection-string --resource-group $resourcegroup --name $storagename --query connectionString --output tsv)
storageKey=$(az storage account keys list --account-name $storagename --query '[0].value')

az functionapp plan create \
  --resource-group $resourcegroup \
  --name badook-func \
  --location $location \
  --number-of-workers 1 \
  --sku EP3 \
  --is-linux


az storage account create --name ${name}logs --resource-group $resourcegroup


funcid=$(az functionapp create \
  --name $name \
  --storage-account ${name}logs \
  --plan badook-func \
  --resource-group $resourcegroup \
  --os-type Linux \
  --runtime python \
  --runtime-version 3.7 \
  --functions-version 3 \
  --deployment-container-image-name gcr.io/badook-cloud-public/blacktransformer:latest --query id --output tsv 2> /dev/null)

if [ ! -z "$vnet" ]
then
  az functionapp vnet-integration add --name $name --resource-group $resourcegroup --vnet $vnet --subnet $subnet
fi

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
  --settings "AZURE_BLOB_ACCOUNT_NAME=$storagename"
  
az functionapp config appsettings set \
  -n $name \
  -g $resourcegroup \
  --settings "AZURE_BLOB_ACCOUNT_KEY=$storageKey"

az functionapp config appsettings set \
  -n $name \
  -g $resourcegroup \
  --settings "incontainer=$incontainer"
  
az functionapp config appsettings set --name $name \
  --resource-group $resourcegroup \
  --settings SCALE_CONTROLLER_LOGGING_ENABLED=AppInsights:Verbose

az functionapp config appsettings set --name $name \
  --resource-group $resourcegroup \
  --settings FUNCTIONS_WORKER_PROCESS_COUNT=1

subjectBeginsWith="/blobServices/default/containers/"$incontainer
storageAccountId=$(az storage account show --name $storagename --resource-group $resourcegroup --query id --output tsv 2> /dev/null)

endpont=${funcid}/functions/new-black-file

sleep 3m

az eventgrid event-subscription create \
  --name "$name-subscription" \
  --source-resource-id $storageAccountId \
  --included-event-types Microsoft.Storage.BlobRenamed Microsoft.Storage.BlobCreated \
  --endpoint $endpont \
  --endpoint-type azurefunction \
  --subject-begins-with $subjectBeginsWith

echo "az eventgrid event-subscription create \
  --name "$name-subscription" \
  --source-resource-id $storageAccountId \
  --included-event-types Microsoft.Storage.BlobRenamed Microsoft.Storage.BlobCreated \
  --endpoint $endpont \
  --endpoint-type azurefunction \
  --subject-begins-with $subjectBeginsWith"
