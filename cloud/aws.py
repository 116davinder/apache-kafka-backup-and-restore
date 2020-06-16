import logging
import boto3
from botocore.exceptions import ClientError
import os
import time
import threading
from common import common

class Upload:

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
        while True:
            _topic_dir = os.path.join(dir, topic_name)
            _count_partition_dirs = len(common.listDirs(_topic_dir))
            _list = common.findFilesInFolder(_topic_dir)
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
            else:
                logging.info(f"s3 upload retry for new files in {retry_upload_seconds} seconds")
                time.sleep(retry_upload_seconds)

class Download:

    def s3_read_checkpoint_partition(dir,topic,partition):
        try:
            logging.info(os.path.join(dir,topic,partition,"checkpoint"))
            with open(os.path.join(dir,topic,partition,"checkpoint")) as c:
                line = c.readline().strip()
                _ck_file = line.split()[0]
                _total_files = line.split()[1]
                return {"checkpoint": _ck_file, "total_files": _total_files}
        except FileNotFoundError as e:
            logging.debug(e)
        return None

    def s3_write_checkpoint_partition(dir,topic,partition,msg):
        try:
            with open(os.path.join(dir,topic,partition,"checkpoint"), "w") as cp:
                cp.write(msg)
        except:
            logging.error(f"writing checkpoint {msg} for {topic}, {partition} is failed")

    def s3_count_partitions(s3_client,bucket,topic):
        try:
            return s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=topic + "/",
                Delimiter='/'
            )['KeyCount']
        except:
            return None

    def s3_list_files(s3_client,bucket,path):
        _list = []
        paginator = s3_client.get_paginator('list_objects_v2')
        operation_parameters = {'Bucket': bucket,'Prefix': path}
        page_iterator = paginator.paginate(**operation_parameters)
        filtered_iterator = page_iterator.search("Contents[?!contains(Key, '.tar.gz.sha256')][]")
        for key_data in filtered_iterator:
            _list.append(key_data['Key'])
        
        logging.debug(sorted(_list))
        return sorted(_list)

    def s3_download(bucket,topic,tmp_dir):
        s3_client = boto3.client('s3')
        _pc = Download.s3_count_partitions(s3_client,bucket,topic)
        if _pc is not None:
            for _pt in range(_pc):
                _ck = Download.s3_read_checkpoint_partition(tmp_dir,topic,str(_pt))
                _partition_path = os.path.join(topic,str(_pt))
                _s3_partition_files = Download.s3_list_files(s3_client,bucket,_partition_path)
                if _ck is not None:
                    try:
                        _s3_partition_files.index(os.path.join(_partition_path,_ck['checkpoint']))
                    except ValueError:
                        logging.error(f"checkout not found in s3 files")

                    logging.info(f"checkpoint {_ck['checkpoint']}, total downloaded files {_ck['total_files']} partition {_pt}")
                else:
                    logging.info(f"reading all files from s3 for partition {_s3_partition_files}")
        else:
            logging.error("No Partitions found")
