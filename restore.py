import os
import logging
import tarfile
import threading
import confluent_kafka
import time
from common import common
from cloud.aws import Download

class KRestore:

    def __init__(self,config):
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
        except:
            self.RETRY_SECONDS = 60
        
        self.FILESYSTEM_TYPE = config['FILESYSTEM_TYPE']
        self.FILESYSTEM_BACKUP_DIR = config['FILESYSTEM_BACKUP_DIR']

        if self.FILESYSTEM_TYPE == "S3":
            self.BUCKET_NAME = config['BUCKET_NAME']

        try:
            self.RESTORE_PARTITION_STRATEGY = config['RESTORE_PARTITION'].lower()
        except:
            self.RESTORE_PARTITION_STRATEGY = "random"

        try:
            self.LOG_LEVEL = config['LOG_LEVEL']
        except:
            self.LOG_LEVEL = logging.INFO

        logging.debug(f"successful loading of all variables")

    def delivery_report(err, msg):
        if err is not None:
            logging.error(f'Message delivery failed: {err}')
        else:
            logging.debug(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    def restore(self):
        _rt = confluent_kafka.Producer(self.PRODUCERCONFIG)
        while True:
            _base_topic_dir = os.path.join(self.BACKUP_DIR,self.BACKUP_TOPIC_NAME)
            _partitions_in_backup_dir = common.listDirs(_base_topic_dir)
            for _p in _partitions_in_backup_dir:
                _partition_dir = os.path.join(_base_topic_dir,_p)
                _partition_backup_files = common.findFilesInFolder(_partition_dir,pattern="*.tar.gz")
                for _file in _partition_backup_files:
                    _file = str(_file)
                    _sha_file = _file + ".sha256"
                    if os.path.getsize(_file) > 0 and os.path.exists(_sha_file):
                        _binFile = common.extractBinFile(_file,_sha_file,_partition_dir)
                        if _binFile is not None:
                            with open(_binFile) as _f:
                                for line in _f.readlines():
                                    line.strip()
                                    _rt.poll(0)
                                    if self.RESTORE_PARTITION == "random":
                                        _rt.produce(
                                            self.RESTORE_TOPIC_NAME,
                                            line.encode('utf-8'),
                                            callback=KRestore.delivery_report
                                        )
                                    elif self.RESTORE_PARTITION == "same":
                                        _rt.produce(
                                            self.RESTORE_TOPIC_NAME,
                                            line.encode('utf-8'),
                                            callback=KRestore.delivery_report,
                                            partition=int(_p)
                                        )
                                    _rt.flush()
                            try:
                                os.remove(_binFile)
                            except FileNotFoundError:
                                pass
                            logging.info(f"restore successful of file {_file}")

            if len(_partition_backup_files) < 2:
                logging.info(f"waiting for more files in {_base_topic_dir}")
                time.sleep(self.RETRY_SECONDS)

def main():

    common.setLoggingFormat()

    try:
        config = common.readJsonConfig(os.sys.argv[1])
    except IndexError as e:
        logging.error(f"restore.json is not passed")
        exit(1)

    b = KRestore(config)
    common.setLoggingFormat(b.LOG_LEVEL)

    if b.FILESYSTEM_TYPE == "S3":
        threading.Thread(
            target=Download.s3_download,
            args=[b.BUCKET_NAME, b.BACKUP_TOPIC_NAME,b.FILESYSTEM_BACKUP_DIR,b.RETRY_SECONDS],
            name="S3 Download"
        ).start()

    _wtk = threading.Thread(
        target=b.restore,
        name="Kafka Producer"
    ).start()

main()