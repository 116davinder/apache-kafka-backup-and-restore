import os
import logging
import threading
from common import common
from library.restore import KRestore


def main():

    common.setLoggingFormat()

    try:
        config = common.readJsonConfig(os.sys.argv[1])
    except IndexError:
        logging.error("restore.json is not passed")
        exit(1)

    b = KRestore(config)
    common.setLoggingFormat(b.LOG_LEVEL)

    os.makedirs(os.path.join(b.BACKUP_DIR, b.BACKUP_TOPIC_NAME), exist_ok=True)

    if b.FILESYSTEM_TYPE == "S3":
        # import only if FS TYPE is Selected
        from cloud import aws

        threading.Thread(
            target=aws.Download.s3_download,
            args=[b.BUCKET_NAME, b.BACKUP_TOPIC_NAME, b.FILESYSTEM_BACKUP_DIR, b.RETRY_SECONDS],
            name="S3 Download"
        ).start()

    elif b.FILESYSTEM_TYPE == "AZURE":
        connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if connect_str is None:
            logging.error("Env Azuure Storage Connection string is missing")
            exit(1)

        # import only if FS TYPE is Selected
        from cloud import azure

        # update azure logger
        logging.getLogger("azure").setLevel(b.LOG_LEVEL)

        threading.Thread(
            target=azure.Download.azure_download,
            args=[connect_str, b.CONTAINER_NAME, b.BACKUP_TOPIC_NAME, b.FILESYSTEM_BACKUP_DIR, b.RETRY_SECONDS],
            name="Azure Download"
        ).start()

    threading.Thread(
        target=b.restore,
        name="Kafka Restore Thread"
    ).start()


if __name__ == "__main__":
    main()
