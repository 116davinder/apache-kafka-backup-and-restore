from common import Common
import os
import logging
import tarfile
import threading

class KRestore:

    def __init__(self,config):
        self.BOOTSTRAP_SERVERS = config['BOOTSTRAP_SERVERS']
        self.RESTORE_TOPIC_NAME = config['RESTORE_TOPIC_NAME']
        self.BACKUP_DIR = config['FILESYSTEM_BACKUP_DIR']
        self.BACKUP_TMP_FILE = os.path.join(self.BACKUP_DIR, "current.bin")
        self.PRODUCERCONFIG = {
            'bootstrap.servers': self.BOOTSTRAP_SERVERS
        }
        logging.info(f"successful loading of all variables")

    def writeToKafka(self):
        _files_in_backup_dir = Common.listFiles(self.BACKUP_DIR)
        for file in _files_in_backup_dir:
            if file.endswith(".tar.gz"):
                file = os.path.join(self.BACKUP_DIR,file)
                _sha_file = file + ".sha256"
                if Common.isSha256HashMatched(file,_sha_file):
                    logging.info(f"reading file & writing to kafka {file}")

def main():

    Common.setLoggingFormat()

    try:
        config = Common.readJsonConfig(os.sys.argv[1])
    except IndexError as e:
        logging.error(f"restore.json is not passed")
        exit(1)

    b = KRestore(config)
    _wtk = threading.Thread(
        target=b.writeToKafka,
        name="Kafka Producer"
    )
    _wtk.start()

main()