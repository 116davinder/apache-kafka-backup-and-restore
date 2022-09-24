import confluent_kafka
import time
from common import common
import os
import logging


class KRestore:

    def __init__(self, config):
        """initialize variables"""
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

        if self.FILESYSTEM_TYPE in ["S3", "MINIO"]:
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
            logging.debug(f'Message delivered to topic: {msg.topic()} and partition: {msg.partition()}')

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
                    logging.info(f"restore successful of already extracted bin {_r_bin_file} file")

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
