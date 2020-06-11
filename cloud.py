import logging
import boto3
from botocore.exceptions import ClientError
import os
import time
from common import Common
import pathlib
import threading
import more_itertools

class Upload:

    def findFiles(dir,pattern="*"):
        _list = []
        result = list(pathlib.Path(dir).rglob(pattern))
        for path in result:
            if os.path.isfile(path):
                _list.append(path)
        return _list

    def s3_upload_file(s3_client,bucket,file_name,object_name):
        try:
            response = s3_client.upload_file(file_name,bucket,object_name)
            logging.info(f"upload successful at s3://{bucket}/{object_name}")
            if not file_name.endswith(".bin"):
                logging.debug(f"deleting uploaded file {file_name}")
                os.remove(file_name)
        except ClientError as e:
            logging.error(f"{file_path} upload failed error {e}")

    def s3_upload(bucket,dir,topic_name,retry_upload_seconds,thread_count):
        s3_client = boto3.client('s3')
        count = 0
        while True:
            _topic_dir = os.path.join(dir, topic_name)
            _count_partition_dirs = len(Common.listDirs(_topic_dir))
            _list = Upload.findFiles(_topic_dir)
            if len(_list) > _count_partition_dirs and threading.active_count() <= thread_count:
                for file_name in _list:
                    file_name = str(file_name)
                    if os.path.getsize(file_name) > 0:
                        object_name = file_name.split(dir)[1]
                        t = threading.Thread(
                            target=Upload.s3_upload_file,
                            args=[s3_client,bucket,file_name,object_name],
                            name="S3 Upload Threads"
                        ).start()
                        count += 1
            else:
                logging.info(f"s3 upload retry for new files in {retry_upload_seconds} seconds")
                time.sleep(retry_upload_seconds)