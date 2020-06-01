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
            return _list
        except FileNotFoundError:
            return []

    def s3_upload_files(bucket,dir,topic_name,retry_upload_seconds):
        s3_client = boto3.client('s3')
        topic_dir = os.path.join(dir, topic_name)
        while True:
            _list = Upload.list_files(topic_dir)
            if _list != ['current.bin']:
                for f in _list:
                    if f.endswith(".tar.gz") or f.endswith(".tar.gz.sha256"):
                        file_path = os.path.join(topic_dir, f)
                        if os.path.getsize(file_path) > 0:
                            try:
                                object_name = os.path.join(topic_name, f)
                                response = s3_client.upload_file(file_path,bucket,object_name)
                                logging.info(f"upload successful at s3://{bucket}/{object_name}")
                                os.remove(file_path)
                            except ClientError as e:
                                logging.error(f"{file_path} upload failed error {e}")
            else:
                logging.info("waiting for new files to be generated")
                time.sleep(retry_upload_seconds)