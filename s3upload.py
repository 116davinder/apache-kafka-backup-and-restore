import logging
import boto3
from botocore.exceptions import ClientError
import sys
import os
import time
import threading

class AWSS3Upload:

    def list_files(dir):
        try:
            _list = os.listdir(dir)
            _list.remove('current.bin')
            return _list
        except:
            return None
 
    def upload_files(bucket,topic_name):
        s3_client = boto3.client('s3')
        while True:
            print(f"number of active threads: {threading.active_count()}")
            _list = AWSS3Upload.list_files("/tmp/" + topic_name)
            if _list is not None:
                for f in _list:
                    try:
                        file_path = "/tmp/" + topic_name + "/" + f
                        object_name = topic_name + "/" + f
                        response = s3_client.upload_file(file_path,bucket,object_name)
                        print(f"upload done for {file_path} and destination path: {object_name}")
                        os.remove(file_path)
                    except ClientError as e:
                        logging.error(e)

            print("all files are uploaded, waiting for new files to be generated")
            time.sleep(10)

def main():
    _upload_thread = threading.Thread(target=AWSS3Upload.upload_files,args=["davinder-test-kafka-backup", "davinder.test"], name="S3-Upload")
    _upload_thread.start()
    print("doing something else")

main()