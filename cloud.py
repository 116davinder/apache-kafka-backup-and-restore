import logging
import boto3
from botocore.exceptions import ClientError
import os
import time
from common import Common
import pathlib
import threading

class Upload:

    def findFiles(dir,pattern="*"):
        _list = []
        result = list(pathlib.Path(dir).rglob(pattern))
        for path in result:
            if os.path.isfile(path):
                _list.append(path)
        return _list

    def s3_upload_files(bucket,dir,topic_name,pattern,retry_upload_seconds):
        s3_client = boto3.client('s3')
        while True:
            _topic_dir = os.path.join(dir, topic_name)
            _count_partition_dirs = len(Common.listDirs(_topic_dir))
            _list = Upload.findFiles(_topic_dir,pattern)
            if len(_list) > _count_partition_dirs:
                for f in _list:
                    f = str(f)
                    if os.path.getsize(f) > 0:
                        try:
                            object_name = f.split(dir)[1]
                            response = s3_client.upload_file(f,bucket,object_name)
                            logging.info(f"upload successful at s3://{bucket}/{object_name}")
                            if not f.endswith(".bin"):
                                logging.debug(f"deleting uploaded file {f}")
                                os.remove(f)
                        except ClientError as e:
                            logging.error(f"{file_path} upload failed error {e}")
            else:
                logging.info("waiting for new files to be generated")
                time.sleep(retry_upload_seconds)