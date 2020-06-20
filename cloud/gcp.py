import logging
import os
import time
import threading
from common import common
from google.cloud import storage

class Upload:

    def gcs_upload_file(gcs_client,bucket,file_name,object_name):

        blob = bucket.blob(object_name)
        blob.upload_from_filename(file_name)
        logging.info(f"upload successful at gcs://{bucket}/{object_name}")
        if not file_name.endswith(".bin"):
            logging.debug(f"deleting uploaded file {file_name}")
            os.remove(file_name)

    def gcs_upload(bucket,dir,topic_name,retry_upload_seconds,thread_count):
        gcs_client = storage.client()
        _bucket = gcs_client.get_bucket(bucket)
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
                        t = threading.Thread(
                            target=gUpload.gcs_upload_file,
                            args=[gcs_client,bucket,file_name,object_name],
                            name="GCS Upload Threads"
                        ).start()
            else:
                logging.info(f"gcs upload retry for new files in {retry_upload_seconds} seconds")
                time.sleep(retry_upload_seconds)

class Download:

    def gcs_list_blobs_with_prefix(gcs_client,bucket,start_offset=None,end_offset=None,prefix=None):
        return gcs_client.list_blobs(
            bucket,
            prefix=prefix,
            delimiter="/",
            start_offset=start_offset,
            end_offset=end_offset
        )
        