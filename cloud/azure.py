import logging
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.core.exceptions import ResourceNotFoundError
import os
import time
import threading
from common import common, checkpoint


class Upload:

    def upload_file(blob_service_client, container_name, file_name, object_name):
        try:
            blob_client = blob_service_client.get_blob_client(
                container_name, blob=object_name)

            with open(file_name, "rb") as data:
                blob_client.upload_blob(data)

            logging.info(f"upload successful {file_name}")

            if not file_name.endswith(".bin"):
                logging.debug(f"deleting uploaded file {file_name}")
                os.remove(file_name)
        except Exception as e:
            logging.error(f"{file_name} upload failed error {e}")

    def upload(connect_str, container_name, dir, topic_name, retry_upload_seconds, thread_count):
        """Main function to initialize azure blob client and
        based on checkpoint file for each partition.
        It will call `upload_file` function to upload.
        It will run after every `retry_upload_seconds`"""
        blob_service_client = BlobServiceClient.from_connection_string(
            connect_str)

        while True:
            _topic_dir = os.path.join(dir, topic_name)
            _count_partition_dirs = len(common.listDirs(_topic_dir))
            _list = common.findFilesInFolder(_topic_dir)
            if len(_list) > _count_partition_dirs and threading.active_count() <= thread_count:
                for file_name in _list:
                    logging.info(file_name)
                    file_name = str(file_name)
                    file_size = os.path.getsize(file_name)
                    if file_size > 0 and file_name.endswith((".tar.gz", ".tar.gz.sha256")):
                        object_name = file_name.split(dir)[1]
                        threading.Thread(
                            target=Upload.upload_file,
                            args=[blob_service_client, container_name,
                                  file_name, object_name],
                            name=f"Azure Upload Thread for {file_name}"
                        ).start()
            else:
                logging.info(
                    f"Azure upload retry for new files in {retry_upload_seconds} seconds")
                time.sleep(retry_upload_seconds)


class Download:

    def get_partitions(container_client, container_name, topic):
        """It will return partitions in a given container and path."""
        try:
            return [i.name for i in container_client.walk_blobs(
                name_starts_with=topic + "/",
                delimiter="/"
            )]
        except Exception as e:
            logging.error(e)
            exit(1)

    def list_files(container_client, prefix):
        """It will list all files for given container and prefix"""
        _list = []
        __all_files = container_client.walk_blobs(
            name_starts_with=prefix,
            delimiter=".tar.gz"
        )

        for file in __all_files:
            _list.append(file.name)

        logging.debug(sorted(_list))
        return sorted(_list)

    def download_file(blob_service_client, container_name, object_path, file_path):
        """It will download two files .tar.gz and .tar.gz.sha256 .

        Parameters
        ----------
        blob_service_client : BlobServiceClient.from_connection_string(connect_str)

        container_name: str

        object_path: str
            Description: path in azure container

        file_path: str
            Description: path from local filesystem
        """
        try:
            # donwload .tar.gz
            blob_client = blob_service_client.get_blob_client(
                container_name, blob=object_path)
            with open(file_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())

            # donwload .tar.gz.sha256
            blob_client_sha = blob_service_client.get_blob_client(
                container_name, blob=object_path + ".sha256")
            with open(file_path + ".sha256", "wb") as download_file:
                download_file.write(blob_client_sha.download_blob().readall())

            logging.info(f"download success for {file_path} and its sha256 file")

        except ResourceNotFoundError as e:
            logging.error(f"No blob found: {e}")

    def azure_download(connect_str, container_name, topic, tmp_dir, retry_download_seconds):
        """It will initialize azure client and
        based on checkpoint file for each partition.
        It will call `download_file` function to download backup
        and backup sha file.
        It will run after every `retry_download_seconds`"""
        blob_service_client = BlobServiceClient.from_connection_string(
            connect_str)

        container_client = ContainerClient.from_connection_string(
            connect_str, container_name=container_name)

        while True:
            _pc = Download.get_partitions(container_client, container_name, topic)
            # create temp. topic directory
            for p in _pc:
                os.makedirs(os.path.join(tmp_dir, str(p)), exist_ok=True)

            for _pt in _pc:
                _topic = _pt.split("/")[0]
                _partition = _pt.split("/")[1]
                _ck = checkpoint.read_checkpoint_partition(tmp_dir, _topic, _partition)
                # _partition_path = os.path.join(topic, str(_pt))
                _partition_files = Download.list_files(container_client, _pt)
                if _ck is not None:
                    logging.debug(f"checkpoint {_ck['checkpoint']}, total downloaded files {_ck['total_files']} partition {_pt}")
                    try:
                        _index = _partition_files.index(_ck['checkpoint']) + 1
                    except ValueError:
                        _index = 0
                        logging.error("checkpoint not found in s3 files")
                else:
                    _ck = {}
                    _ck['checkpoint'] = ""
                    _ck['total_files'] = 0
                    _index = 0

                logging.info(f"Total Files: {len(_partition_files)}, partition: {_partition}, files to download: {len(_partition_files[_index:])}")

                try:
                    _ck['total_files'] = int(_ck['total_files'])
                except ValueError as e:
                    logging.error(e)

                if _ck['total_files'] < len(_partition_files):
                    for file in _partition_files[_index + 1:]:
                        Download.download_file(blob_service_client, container_name, file, os.path.join(tmp_dir, file))
                        if file.endswith(".tar.gz"):
                            _ck['total_files'] += 1
                            checkpoint.write_checkpoint_partition(
                                tmp_dir,
                                _topic,
                                _partition,
                                file + " " + str(_ck['total_files'])
                            )

            if len(_pc) == 0:
                logging.error(f"No Partitions found in container: {container_name}, topic: {topic}")
                exit(1)

            logging.info(f"retry for new file after {retry_download_seconds}s in Azure {container_name}/{topic}")
            time.sleep(retry_download_seconds)
