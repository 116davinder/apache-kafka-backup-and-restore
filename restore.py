import os
import logging
import threading
import confluent_kafka
import time
from common import common


class KRestore:

    def __init__(self, config):
        self.BOOTSTRAP_SERVERS = config['BOOTSTRAP_SERVERS']
        self.BACKUP_TOPIC_NAME = config['BACKUP_TOPIC_NAME']
        self.RESTORE_TOPIC_NAME = config['RESTORE_TOPIC_NAME']
        self.BACKUP_DIR = config['FILESYSTEM_BACKUP_DIR']

        self.PRODUCERCONFIG = {
            'bootstrap.servers': self.BOOTSTRAP_SERVERS,
            'enable.idempotence': True,
        }
        try:
            self.RETRY_SECONDS = config['RETRY_SECONDS']
        except KeyError:
            self.RETRY_SECONDS = 60

        self.FILESYSTEM_TYPE = config['FILESYSTEM_TYPE']
        self.FILESYSTEM_BACKUP_DIR = config['FILESYSTEM_BACKUP_DIR']

        if self.FILESYSTEM_TYPE == "S3":
            self.BUCKET_NAME = config['BUCKET_NAME']

        elif self.FILESYSTEM_TYPE == "AZURE":
            self.CONTAINER_NAME = config['CONTAINER_NAME']

        try:
            self.RESTORE_PARTITION_STRATEGY = config['RESTORE_PARTITION'].lower()
        except KeyError:
            self.RESTORE_PARTITION_STRATEGY = "random"

        try:
            self.LOG_LEVEL = config['LOG_LEVEL']
        except KeyError:
            self.LOG_LEVEL = logging.INFO

        logging.debug("successful loading variables")

    def delivery_report(err, msg):
        if err is not None:
            logging.error(f'Message delivery failed: {err}')
        else:
            logging.debug(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    def write_to_kafka(rt,binFile,partition,topic,rts):
        if binFile is not None:
            with open(binFile) as _f:
                for line in _f.readlines():
                    line.strip()
                    rt.poll(0)
                    if rts == "random":
                        rt.produce(
                            topic,
                            line.encode('utf-8'),
                            callback=KRestore.delivery_report
                        )
                    elif rts == "same":
                        rt.produce(
                            topic,
                            line.encode('utf-8'),
                            callback=KRestore.delivery_report,
                            partition=int(partition)
                        )
                    rt.flush()
            try:
                os.remove(binFile)
            except FileNotFoundError:
                pass

    def restore(self):
        _rt = confluent_kafka.Producer(self.PRODUCERCONFIG)
        while True:
            _base_topic_dir = os.path.join(self.BACKUP_DIR, self.BACKUP_TOPIC_NAME)
            _partitions_in_backup_dir = common.listDirs(_base_topic_dir)
            for _p in _partitions_in_backup_dir:
                _partition_dir = os.path.join(_base_topic_dir, _p)
                _partition_backup_files = common.findFilesInFolder(_partition_dir, pattern="*.tar.gz")

                # restore already extracted files
                _partition_backup_bin_files = common.findFilesInFolder(_partition_dir, pattern="*.bin")
                for _r_bin_file in _partition_backup_bin_files:
                    KRestore.write_to_kafka(
                        _rt,
                        _r_bin_file,
                        _p,
                        self.RESTORE_TOPIC_NAME,
                        self.RESTORE_PARTITION_STRATEGY
                    )
                    logging.info(f"restore successful of file {_r_bin_file}.tar.gz")

                # restore new .tar.gz files
                for _file in _partition_backup_files:
                    _file = str(_file)
                    _sha_file = _file + ".sha256"
                    if os.path.getsize(_file) > 0 and os.path.exists(_sha_file):
                        _binFile = common.extractBinFile(_file, _sha_file, _partition_dir)
                        KRestore.write_to_kafka(
                            _rt,
                            _binFile,
                            _p,
                            self.RESTORE_TOPIC_NAME,
                            self.RESTORE_PARTITION_STRATEGY
                        )
                        logging.info(f"restore successful of file {_file}")

            logging.info(f"retry for more files in {_base_topic_dir} after {self.RETRY_SECONDS}")
            time.sleep(self.RETRY_SECONDS)


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
