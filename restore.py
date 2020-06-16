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

        logging.info(f"successful loading of all variables")

    def delivery_report(err, msg):
        if err is not None:
            logging.error(f'Message delivery failed: {err}')
        else:
            logging.debug(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    def restore(self):
        _rt = confluent_kafka.Producer(self.PRODUCERCONFIG)
        while True:
            _files_in_backup_dir = common.listDirs(os.path.join(self.BACKUP_DIR,self.BACKUP_TOPIC_NAME))
            for file in _files_in_backup_dir:
                    file = os.path.join(self.BACKUP_DIR,file)
                    if file.endswith("tar.gz"):
                        logging.debug(f"processing file {file}")
                        _sha_file = file + ".sha256"
                        if os.path.getsize(file) > 0 and os.path.exists(_sha_file):
                            binFile = common.extractBinFile(file,_sha_file,self.BACKUP_DIR)
                            if binFile is not None:
                                with open(binFile) as _f:
                                    for line in _f.readlines():
                                        line.strip()
                                        _rt.poll(0)
                                        _rt.produce(
                                            self.RESTORE_TOPIC_NAME,
                                            line.encode('utf-8'),
                                            callback=KRestore.delivery_report
                                        )
                                _rt.flush()
                                try:
                                    os.remove(binFile)
                                except FileNotFoundError:
                                    pass
                                logging.info(f"restore successful of file {file}")
            if len(_files_in_backup_dir) < 2:
                logging.info(f"waiting for more files in {self.BACKUP_DIR}")
                time.sleep(self.RETRY_SECONDS)

def main():

    common.setLoggingFormat()

    try:
        config = common.readJsonConfig(os.sys.argv[1])
    except IndexError as e:
        logging.error(f"restore.json is not passed")
        exit(1)

    b = KRestore(config)
   
    if b.FILESYSTEM_TYPE == "S3":
        threading.Thread(
            target=Download.s3_download,
            args=[b.BUCKET_NAME, b.BACKUP_TOPIC_NAME,b.FILESYSTEM_BACKUP_DIR,b.RETRY_SECONDS],
            name="S3 Download"
        ).start()

    # _wtk = threading.Thread(
    #     target=b.restore,
    #     name="Kafka Producer"
    # ).start()

main()