import confluent_kafka
from datetime import datetime
import tarfile
import hashlib
from os import mkdir,sys
import json

class KBackup:
    def __init__(self,configFilePath):
        try:
            with open(configFilePath) as cf:
                _config = json.load(cf)
        except:
            print("unable to load config.json")
            exit(1)

        self.BOOTSTRAP_SERVERS = _config['BOOTSTRAP_SERVERS']
        self.GROUP_ID = _config['GROUP_ID']
        self.TOPIC_NAME_LIST = _config['TOPIC_NAMES']
        self.BACKUP_DIR = _config['FILESYSTEM_BACKUP_DIR'] + self.TOPIC_NAME_LIST[0]
        self.BACKUP_TMP_FILE = self.BACKUP_DIR + "current.bin"
        self.FILESYSTEM_TYPE = _config['FILESYSTEM_TYPE']

        self.CONSUMERCONFIG = {
            'bootstrap.servers': self.BOOTSTRAP_SERVERS,
            'group.id': self.GROUP_ID,
            'auto.offset.reset': 'earliest'
        }

    def __calculateSha256(self, file):
        with open(file,"rb") as f:
            return hashlib.sha256(f.read()).hexdigest();

    def __createSha256OfBackupFile(self, file):
        with open(file + ".sha256", "w") as f:
            f.write(self.__calculateSha256(file))

    def __writeDataToKafkaBinFile(self,msg,mode):
        with open(self.BACKUP_TMP_FILE, mode) as f:
            try:
                f.write(msg.value().decode('utf-8'))
                f.write("\n")
            except:
                if mode != "w":
                    print("unable to write to new file")
                else:
                    print("unable to append to current.bin file")

    def __createTarGz(self):
        file = self.BACKUP_DIR + "/" + datetime.now().strftime("%Y%M%d-%H%M%S") + ".tar.gz"
        _t = tarfile.open(file, "w:gz")
        _t.add(self.BACKUP_TMP_FILE)
        _t.close()
        print(f"Created Successful Backupfile: {file}")
        self.__createSha256OfBackupFile(file)
        print(f"Created Successful Backup sha256 file: {file}.sha256")

    def __createBackupTopicDir(self):
        try:
            mkdir(self.BACKUP_DIR)
        except FileExistsError:
            pass

    def readFromTopic(self):
        _rt = confluent_kafka.Consumer(self.CONSUMERCONFIG)
        _rt.subscribe(self.TOPIC_NAME_LIST)

        self.__createBackupTopicDir()

        count = 0
        while True:
            msg = _rt.poll(timeout=5.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer Error: {msg.error()}")
                continue

            if count == 0:
                self.__writeDataToKafkaBinFile(msg, "a+")
            if count > 0:
                if count % 50 == 0:
                    self.__createTarGz()
                    self.__writeDataToKafkaBinFile(msg, "w")
                else:
                    self.__writeDataToKafkaBinFile(msg, "a+")
            count += 1

        _rt.close()

def main():
    configFilePath = sys.argv[1]
    b = KBackup(configFilePath)
    b.readFromTopic()

main()
