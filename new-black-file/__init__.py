import logging
import pysqlite3 as sqlite3
import azure.functions as func

logging.info("started black transformer app")

def main(myblob: func.InputStream, doc: func.Out[func.Document]):
    logging.info(f"Python blob trigger function processed blob \n"
                 f"Name: {myblob.name}\n"
                 f"Blob Size: {myblob.length} bytes")

    # conn = sqlite3.connect(f'{myblob.name}')
    # conn.enable_load_extension(True)
    # conn.load_extension("mod_spatialite")
