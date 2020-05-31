import logging
import boto3
from botocore.exceptions import ClientError
import sys
import os
import time
import threading

class Upload:

    def list_files(dir):
        try:
            _list = os.listdir(dir)
            _list.remove('current.bin')
            return _list
        except FileNotFoundError:
            return []
 
    def s3_upload_files(bucket,dir,topic_name):
        s3_client = boto3.client('s3')
        while True:
            _list = Upload.list_files(dir + topic_name)
            if _list != []:
                for f in _list:
                    try:
                        file_path = dir + topic_name + "/" + f
                        object_name = topic_name + "/" + f
                        response = s3_client.upload_file(file_path,bucket,object_name)
                        logging.info(f"upload done for {file_path} at destination path {object_name}")
                        os.remove(file_path)
                    except ClientError as e:
                        logging.error(f"file upload failed error {e}")
            else:
                logging.info("waiting for new files to be generated")
                time.sleep(10)