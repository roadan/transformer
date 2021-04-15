import sys
import logging
import sqlite3
import azure.functions as func
import pandas as pd
import os 
import base64
import uuid
import glob
import io
import json 
import gc
import shutil
import sqlalchemy as sa

from azure.storage.blob import BlobServiceClient, BlobBlock
from io import BytesIO
import dask.dataframe as da
from urllib.parse import urlparse

def main(event: func.EventGridEvent) -> None:

    data = event.get_json()
    name = os.path.basename(data['url'])

    """ Writinh the blob db to /tmp """
    download_chunks(name, os.environ['incontainer'], os.environ['badookinstore'])

    """ Exporting to parquet and uploading """
    db_path = f'/tmp/{name}'
    output_path = f'{name}-parquet'
    
    export_parquet(db_path, output_path)

    """ cleaning up """
    if os.path.exists(db_path):
        os.remove(db_path)

#@profile
def download_chunks(file_name, container, conn):
    blob_service = BlobServiceClient.from_connection_string(conn)
    blob_client = blob_service.get_blob_client(container=container, blob=file_name)
    
    blob_poperties = blob_client.get_blob_properties()
    blob_size = blob_poperties.size
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
            b = downloader.readall()
            file.write(b)
            start += bytesToFetch
            bytesRemaining -= bytesToFetch
            #print(f'{bytesRemaining} left')
            del downloader
            del b
            del blob_client
            del blob_service
        del file
    gc.collect()

def export_parquet(db_path, output_path):
    batch_size = 500000
    i = 1
    query = f'SELECT * from trackPoints order by timestamp limit {batch_size}'
    with sqlite3.connect(db_path) as db:
        lasttime = 0
        while True:
            if lasttime != 0:
                query = f'SELECT * from trackPoints WHERE timestamp > \'{lasttime}\' order by timestamp limit {batch_size}'
            
            df = pd.read_sql_query(query, db)
            print(f'------> {len(df)}')
            print(f'------> {i}')
            if len(df) == 0:
                break

            ddf = da.from_pandas(df, chunksize=20000)
# ddf = da.read_sql_table('trackPoints', f'sqlite:///{db_path}', index_col='fromPositionX',#, engine_kwargs={'connect_args': {'detect_types': sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES}, 'native_datetime': True})
#         columns=['uuid', 'localTrackUuid', 'trackUuid', sa.sql.column('timestamp').cast(sa.types.String).label('timestamp'), 'sourceNodeUuid', 'fromPositionX', 'fromPositionY', 'toPositionX', 'toPositionY' ])  
#dff = dff.repartition(10000)
            account = os.environ['AZURE_BLOB_ACCOUNT_NAME'] 
            account_key = os.environ['AZURE_BLOB_ACCOUNT_KEY']
            container = os.environ['badookoutstore']

            storage_options={'account_name': account, 'account_key': account_key}

            #ddf.to_parquet(f'abfs://{container}/{output_path}/{i}', storage_options=storage_options)
            lasttime = df["timestamp"].max()
        # upload(f'{output_path}/')
        # shutil.rmtree(f'{output_path}/')
            i+=1
            if len(df) < batch_size:
                break
    del db

if __name__ == "__main__":
    argv = sys.argv
    file_name = argv[1] 
    container = argv[2]
    conn = argv[3]

#     found_objects = gc.get_objects()
#     print('%d objects before' % len(found_objects))

#     download_chunks(file_name, container, conn )

#     found_objects = gc.get_objects()
#     print('%d objects after' % len(found_objects))

#     gc.collect()
#     found_objects = gc.get_objects()
#     print('%d objects after gc' % len(found_objects))

    db_path = f'/tmp/{file_name}'
    output_path = f'{file_name}.parquet'
    export_parquet(db_path, output_path)
    if os.path.exists(db_path):
        print('-------------------------------- done --------------------------------')
        print(db_path)
        os.remove(db_path)

#     found_objects = gc.get_objects()
#     print('%d objects after parquet' % len(found_objects))
#     upload(file_name, res)

#     found_objects = gc.get_objects()
#     print('%d objects after upload' % len(found_objects))