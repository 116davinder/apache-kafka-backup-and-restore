import logging
import boto3
from botocore.exceptions import ClientError,NoCredentialsError
import os
import time
import threading
from common import common, checkpoint


class Upload:

    def s3_upload_file(s3_client,bucket,file_name,file_object_name, sha_file_name, sha_file_object_name):
        """It will upload given `file_name` to given s3 `bucket`
        and `object_name` s3 path.
        """

        try:
            s3_client.upload_file(file_name,bucket,file_object_name)
            logging.info(f"upload successful at s3://{bucket}/{file_object_name}")
            s3_client.upload_file(sha_file_name,bucket,sha_file_object_name)
            logging.info(f"upload successful at s3://{bucket}/{sha_file_object_name}")
            os.remove(file_name)
            os.remove(sha_file_name)
        except ClientError as e:
            logging.error(f"{file_name} upload failed error {e}")

    def s3_upload(bucket,dir,topic_name,retry_upload_seconds,thread_count):
        """It will initialize s3 client and
        based on checkpoint file for each partition.
        It will call `s3_upload_file` function to upload.

        It will run after every `retry_upload_seconds`"""

        # s3_client = boto3.client('s3', endpoint_url="http://localhost:4566", use_ssl=False) can be used for localstack testing
        s3_client = boto3.client('s3')
        while True:
            _topic_dir = os.path.join(dir, topic_name)
            _list = common.findFilesInFolder(_topic_dir, pattern="*.tar.gz")
            logging.debug(f"pending files to upload {len(_list)} and number of active threads {threading.active_count()}")
            if threading.active_count() <= thread_count:
                for file_name in _list:
                    file_name = str(file_name)
                    file_object_name = file_name.split(dir)[1]
                    sha_file_name = file_name + ".sha256"
                    sha_file_object_name = file_object_name + ".sha256"
                    if common.isFileAndShaFileExist(file_name, sha_file_name):
                        logging.debug(f"start upload of file {file_name}")
                        threading.Thread(
                            target=Upload.s3_upload_file,
                            args=[s3_client,bucket,file_name,file_object_name, sha_file_name, sha_file_object_name],
                            name="S3 Upload Thread"
                        ).start()

            logging.info(f"s3 upload retry for new files in {retry_upload_seconds} seconds")
            time.sleep(retry_upload_seconds)


class Download:

    def s3_count_partitions(s3_client,bucket,topic):
        """It will return number of objects in a given s3 bucket and s3 bucket path."""

        try:
            return s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=topic + "/",
                Delimiter='/'
            )['KeyCount']
        except NoCredentialsError as e:
            logging.error(e)
            exit(1)

    def s3_list_files(s3_client,bucket,path):
        """It will list all files for given s3 bucket and s3 bucket path."""

        _list = []
        paginator = s3_client.get_paginator('list_objects_v2')
        operation_parameters = {'Bucket': bucket,'Prefix': path}
        page_iterator = paginator.paginate(**operation_parameters)
        search_condition = "Contents[?!contains(Key, '.tar.gz.sha256') && !contains(Key, '.bin') && !contains(Key, '.checkpoint')][]"
        filtered_iterator = page_iterator.search(search_condition)
        for key_data in filtered_iterator:
            if key_data:
                _list.append(key_data['Key'])

        logging.debug(sorted(_list))
        return sorted(_list)

    def s3_download_file(s3_client,bucket,object_path,file_path):
        """It will download two files .tar.gz and .tar.gz.sha256 .

        Parameters
        ----------
        s3_client : boto3.client('s3')

        bucket: str

        object_path: str
            Description: path in s3 bucket

        file_path: str
            Description: path from local filesystem
        """

        try:
            # donwload .tar.gz
            s3_client.download_file(bucket, object_path, file_path)
            # download .tar.gz.sha256
            s3_client.download_file(bucket, object_path + ".sha256", file_path + ".sha256")
            logging.info(f"download success for {file_path} and its sha256 file ")
        except ClientError as e:
            logging.error(f"{file_path} failed with error {e}")

    def s3_download(bucket,topic,tmp_dir,retry_download_seconds=60):
        """It will initialize s3 client and
        based on checkpoint file for each partition.
        It will call `s3_download_file` function to download backup
        and backup sha file.

        It will run after every `retry_download_seconds`"""

        s3_client = boto3.client('s3')
        while True:
            _pc = Download.s3_count_partitions(s3_client,bucket,topic)
            # create temp. topic directory
            for p in range(_pc):
                os.makedirs(os.path.join(tmp_dir,topic,str(p)),exist_ok=True)

            for _pt in range(_pc):

                _ck = checkpoint.read_checkpoint_partition(tmp_dir,topic,str(_pt))
                _partition_path = os.path.join(topic,str(_pt))
                _s3_partition_files = Download.s3_list_files(s3_client,bucket,_partition_path)
                if _ck is not None:
                    logging.debug(f"checkpoint {_ck['checkpoint']}, total downloaded files {_ck['total_files']} partition {_pt}")
                    try:
                        _index = _s3_partition_files.index(_ck['checkpoint']) + 1
                    except ValueError:
                        _index = 0
                        logging.error(f"checkpoint not found in s3 files")
                else:
                    _ck = {}
                    _ck['checkpoint'] = ""
                    _ck['total_files'] = 0
                    _index = 0

                logging.debug(f"Total Files: {len(_s3_partition_files)}, partition: {_pt}, files to download: {len(_s3_partition_files[_index:])}")

                try:
                    _ck['total_files'] = int(_ck['total_files'])
                except ValueError as e:
                    logging.error(e)

                if _ck['total_files'] < len(_s3_partition_files):
                    for file in _s3_partition_files[_index + 1:]:
                        Download.s3_download_file(s3_client,bucket,file,os.path.join(tmp_dir,file))
                        if file.endswith(".tar.gz"):
                            _ck['total_files'] += 1
                            checkpoint.write_checkpoint_partition(tmp_dir,topic,str(_pt),file + " " + str(_ck['total_files']))

            if _pc == 0:
                logging.error(f"No Partitions found in given S3 path s3://{bucket}/{topic} retry seconds {retry_download_seconds}s")
                exit(1)

            logging.info(f"retry for new file after {retry_download_seconds}s in s3://{bucket}/{topic}")
            time.sleep(retry_download_seconds)
