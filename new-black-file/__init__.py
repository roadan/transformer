import sys
import logging
import spatialite
import azure.functions as func
import pandas as pd
import os 
import base64
import uuid
import glob
import io

from azure.storage.blob import BlobServiceClient, BlobBlock
from io import BytesIO
import dask.dataframe as da


logging.info("started black transformer app")
logging.info("-----------------------------")

def main(myblob: func.InputStream) -> None:
    logging.info(f"Python blob trigger function processed blob \n"
                 f"Name: {myblob.name}\n"
                 f"Blob Size: {myblob.length} bytes")

    name = os.path.relpath(myblob.name, os.environ['incontainer'])

    """ Writinh the blob db to /tmp """
    download_chunks(name, os.environ['incontainer'], os.environ['badookinstore'], myblob.length)

    """ Exporting to parquet and uploading """
    db_path = f'/tmp/{name}'
    output_path = f'{name}.parquet'
    res = export_parquet(db_path, output_path)
    upload(name, res, db_path)

    """ cleaning up """
    if os.path.exists(db_path):
        os.remove(db_path)

def download_chunks(file_name, container, conn, blob_size):
    blob_service = BlobServiceClient.from_connection_string(conn)
    blob_client = blob_service.get_blob_client(container=container, blob=file_name)

    bytesRemaining = blob_size
    bytesToFetch = 0  
    start = 0 
    chunk_size = 1024*1024
    
    with open(f'/tmp/{file_name}', 'wb') as file:
        while bytesRemaining > 0:
            if bytesRemaining < chunk_size:
                bytesToFetch = bytesRemaining
            else:
                bytesToFetch = chunk_size

            downloader = blob_client.download_blob(start,bytesToFetch)
            file.write(downloader.readall())
            start += bytesToFetch
            bytesRemaining -= bytesToFetch
            print(f'{bytesRemaining} left')


def export_parquet(db_path, output_path):
    with spatialite.connect(db_path) as db:
        df = pd.read_sql_query("SELECT uuid, timestamp, hasLine, ST_X(fromPosition) as positionX, ST_Y(fromPosition) as positionY, fromAltitude, toAltitude, detectionUuid, bestClassification, trackUuid, previousTrackPointUuid, isKeyPoint, localTrackUuid, sourceNodeUuid from rawTrackPoints", db)
        ddf = da.from_pandas(df, chunksize=30000)
        ddf.to_parquet(f'{output_path}/')
        return f'{output_path}/'

def upload(name, root_path, db_path):
    blob_service = BlobServiceClient.from_connection_string(os.environ['badookinstore'])
    container_name = os.environ['badookoutstore']
    files = [f for f in glob.glob(root_path + "**/*.parquet", recursive=True)]

    for f in files:
        with open(f, 'rb') as data:
            print(f'file: {f}')
            blob_client = blob_service.get_blob_client(container=container_name, blob=f)
            blob_client.upload_blob(data)
    
# if __name__ == "__main__":
#     argv = sys.argv
#     file_name = argv[1] 
#     container = argv[2]
#     conn = argv[3]

#     blob_service = BlobServiceClient.from_connection_string(conn)
#     blob_client = blob_service.get_blob_client(container=container, blob=file_name)
#     blob_poperties=blob_client.get_blob_properties()
#     blob_size=blob_poperties.size
    
#     download_chunks(file_name, container, conn, blob_size)
    # print(f'db_path: {db_path}, output_path {output_path}') 
    # res = export_parquet(db_path, output_path)
    # print(f'------------ res: {res}')
    # upload(output_path, res, db_path)