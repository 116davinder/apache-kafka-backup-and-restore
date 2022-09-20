import os
import logging
import threading
from common import common
from library.backup import KBackup


def main():

    common.setLoggingFormat()
    try:
        config = common.readJsonConfig(os.sys.argv[1])
    except IndexError:
        logging.error("backup.json is not passed")
        exit(1)

    b = KBackup(config)
    common.setLoggingFormat(b.LOG_LEVEL)

    for _r_thread in range(b.NUMBER_OF_KAFKA_THREADS):
        _r_thread = threading.Thread(
            target=b.backup,
            name="Kafka Consumer " + str(_r_thread)
        )
        _r_thread.start()

    if config['FILESYSTEM_TYPE'] == "S3":
        # import only if FS TYPE is Selected
        from cloud import aws
        try:
            bucket = config['BUCKET_NAME']
            tmp_dir = config['FILESYSTEM_BACKUP_DIR']
            topic_name = config['TOPIC_NAMES'][0]
            try:
                retry_upload_seconds = config['RETRY_UPLOAD_SECONDS']
                logging.debug(f"RETRY_UPLOAD_SECONDS is set to {config['RETRY_UPLOAD_SECONDS']}")
            except KeyError:
                logging.debug("setting RETRY_UPLOAD_SECONDS to default 60")
                retry_upload_seconds = 60

            aws.Upload.s3_upload(
                bucket,
                tmp_dir,
                topic_name,
                retry_upload_seconds,
                b.NUMBER_OF_KAFKA_THREADS + 1
            )

        except KeyError as e:
            logging.error(f"unable to set s3 required variables {e}")

    elif config['FILESYSTEM_TYPE'] == "AZURE":

        connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if connect_str is None:
            logging.error("Env Azure Storage Connection string is missing")
            exit(1)

        # import only if FS TYPE is Selected
        from cloud import azure

        # update azure logger
        logging.getLogger("azure").setLevel(b.LOG_LEVEL)

        try:
            container_name = config['CONTAINER_NAME']
            tmp_dir = config['FILESYSTEM_BACKUP_DIR']
            topic_name = config['TOPIC_NAMES'][0]
            try:
                retry_upload_seconds = config['RETRY_UPLOAD_SECONDS']
                logging.debug(f"RETRY_UPLOAD_SECONDS is set to {config['RETRY_UPLOAD_SECONDS']}")
            except KeyError:
                logging.debug("setting RETRY_UPLOAD_SECONDS to default 60")
                retry_upload_seconds = 60

            azure.Upload.upload(
                connect_str,
                container_name,
                tmp_dir,
                topic_name,
                retry_upload_seconds,
                b.NUMBER_OF_KAFKA_THREADS + 1
            )

        except KeyError as e:
            logging.error(f"unable to set azure required variables {e}")


if __name__ == "__main__":
    main()
