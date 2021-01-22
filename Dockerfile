FROM mcr.microsoft.com/azure-functions/python:3.0-python3.7-appservice
ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
AzureFunctionsJobHost__Logging__Console__IsEnabled=true

RUN apt-get update && apt-get install -y libsqlite3-mod-spatialite
RUN apt-get update && apt-get install -y libspatialite-dev
RUN ln -s /lib/x86_64-linux-gnu/mod_spatialite.so /usr/lib/x86_64-linux-gnu/mod_spatialite

COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY new-black-file/* /home/site/wwwroot/