import logging
import boto3
from botocore.exceptions import ClientError
import os
import time
from common import Common

class Upload:

    def s3_upload_files(bucket,dir,topic_name,retry_upload_seconds):
        s3_client = boto3.client('s3')
        topic_dir = os.path.join(dir, topic_name)
        while True:
            _list = Common.listFiles(topic_dir)
            if len(_list) > 1:
                for f in _list:
                        file_path = os.path.join(topic_dir, f)
                        if os.path.getsize(file_path) > 0:
                            try:
                                object_name = os.path.join(topic_name, f)
                                response = s3_client.upload_file(file_path,bucket,object_name)
                                logging.info(f"upload successful at s3://{bucket}/{object_name}")
                                if f != "current.bin":
                                    os.remove(file_path)
                            except ClientError as e:
                                logging.error(f"{file_path} upload failed error {e}")
            else:
                logging.info("waiting for new files to be generated")
                time.sleep(retry_upload_seconds)