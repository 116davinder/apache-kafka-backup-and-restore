import logging
from minio import Minio
from minio.error import MinioException
import os
import time
import threading
from common import common, checkpoint


class Upload:

    def minio_upload_file(minio_client,bucket,file_name,object_name):
        """It will upload given `file_name` to given minio `bucket`
        and `object_name` minio bucket path.
        """

        try:
            minio_client.fput_object(bucket,object_name,file_name)
            logging.info(f"upload successful at minio://{bucket}/{object_name}")
            if not file_name.endswith(".bin"):
                logging.debug(f"deleting uploaded file {file_name}")
                os.remove(file_name)
        except MinioException as e:
            logging.error(f"{file_name} upload failed error {e}")

    def minio_upload(
            minio_url,
            is_mino_secure,
            minio_access_key,
            minio_secret_key,
            bucket,
            dir,
            topic_name,
            retry_upload_seconds,
            thread_count
        ):
        """It will initialize minio client and
        based on checkpoint file for each partition.
        It will call `minio_upload_file` function to upload.

        It will run after every `retry_upload_seconds`"""

        minio_client = Minio(
            minio_url,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=is_mino_secure
        )
        while True:
            _topic_dir = os.path.join(dir, topic_name)
            _count_partition_dirs = len(common.listDirs(_topic_dir))
            _list = common.findFilesInFolder(_topic_dir)
            if len(_list) > _count_partition_dirs and threading.active_count() <= thread_count:
                for file_name in _list:
                    file_name = str(file_name)
                    file_size = os.path.getsize(file_name)
                    if ( file_size > 0 and file_name.endswith(".tar.gz")
                        or
                        file_size > 0 and file_name.endswith(".tar.gz.sha256")):
                        object_name = file_name.split(dir)[1]
                        threading.Thread(
                            target=Upload.minio_upload_file,
                            args=[minio_client,bucket,file_name,object_name],
                            name="MINIO Upload Threads"
                        ).start()
            else:
                logging.info(f"minio upload retry for new files in {retry_upload_seconds} seconds")
                time.sleep(retry_upload_seconds)


class Download:

    def minio_count_partitions(minio_client,bucket,topic):
        """It will return number of objects in a given minio bucket and minio bucket path."""

        return len(list(minio_client.list_objects(bucket, prefix=topic + "/")))

    def minio_list_files(minio_client,bucket,path):
        """It will list all files for given minio bucket which endswith tar.gz and minio bucket path."""

        _list = []

        for obj in minio_client.list_objects(bucket, path, recursive=True):
            if obj.object_name.endswith(".tar.gz"):
                _list.append(obj.object_name)

        logging.debug(_list)
        return _list

    def minio_download_file(minio_client,bucket,object_path,file_path):
        """It will download two files .tar.gz and .tar.gz.sha256 .

        Parameters
        ----------
        minio_client : minio.Minio()

        bucket: str

        object_path: str
            Description: path in minio bucket

        file_path: str
            Description: path from local filesystem
        """

        try:
            # donwload .tar.gz
            minio_client.fget_object(bucket, object_path, file_path)
            # download .tar.gz.sha256
            minio_client.fget_object(bucket, object_path + ".sha256", file_path + ".sha256")
            logging.info(f"download success for {file_path} and its sha256 file ")
        except MinioException as e:
            logging.error(f"{file_path} failed with error {e}")

    def minio_download(
            minio_url,
            is_mino_secure,
            minio_access_key,
            minio_secret_key,
            bucket,
            topic,
            tmp_dir,
            retry_download_seconds=60
        ):
        """It will initialize minio client and
        based on checkpoint file for each partition.
        It will call `minio_download_file` function to download backup
        and backup sha file.

        It will run after every `retry_download_seconds`"""

        minio_client = Minio(
            minio_url,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=is_mino_secure
        )

        if not minio_client.bucket_exists(bucket):
            logging.error(f"{bucket} bucket doesn't exist")
            exit(1)

        while True:
            _pc = Download.minio_count_partitions(minio_client, bucket, topic)
            # create temp. topic directory
            for p in range(_pc):
                os.makedirs(os.path.join(tmp_dir,topic,str(p)),exist_ok=True)

            for _pt in range(_pc):

                _ck = checkpoint.read_checkpoint_partition(tmp_dir,topic,str(_pt))
                _partition_path = os.path.join(topic,str(_pt))
                _minio_partition_files = Download.minio_list_files(minio_client, bucket, _partition_path)
                if _ck is not None:
                    logging.debug(f"checkpoint {_ck['checkpoint']}, total downloaded files {_ck['total_files']} partition {_pt}")
                    try:
                        _index = _minio_partition_files.index(_ck['checkpoint']) + 1
                    except ValueError:
                        _index = 0
                        logging.error(f"[Not Found] checkpoint: {_ck['checkpoint']}, topic: {topic}, partition {_pt} in the given bucket: {bucket}")
                else:
                    _ck = {}
                    _ck['checkpoint'] = ""
                    _ck['total_files'] = 0
                    _index = 0

                logging.debug(f"Total Files: {len(_minio_partition_files)}, partition: {_pt}, files to download: {len(_minio_partition_files[_index:])}")

                try:
                    _ck['total_files'] = int(_ck['total_files'])
                except ValueError as e:
                    logging.error(e)

                if _ck['total_files'] < len(_minio_partition_files):
                    for file in _minio_partition_files[_index + 1:]:
                        Download.minio_download_file(minio_client, bucket, file, os.path.join(tmp_dir,file))
                        _ck['total_files'] += 1
                        checkpoint.write_checkpoint_partition(tmp_dir,topic,str(_pt),file + " " + str(_ck['total_files']))

            if _pc == 0:
                logging.error(f"No Partitions found in given minio path minio://{bucket}/{topic} retry seconds {retry_download_seconds}s")
                exit(1)

            logging.info(f"retry for new file after {retry_download_seconds}s in minio://{bucket}/{topic}")
            time.sleep(retry_download_seconds)
