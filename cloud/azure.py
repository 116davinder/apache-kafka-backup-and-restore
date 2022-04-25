import logging
from azure.storage.blob import BlobServiceClient
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
