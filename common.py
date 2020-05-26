from hashlib import sha256
from datetime import datetime
from os import mkdir
import tarfile
import json

class Common:

    def readJsonConfig(file):
        try:
            with open(file) as cf:
                return json.load(cf)
        except:
            print("unable to load config.json")
            exit(1)

    def calculateSha256(file):
        with open(file,"rb") as f:
            return sha256(f.read()).hexdigest();

    def createSha256OfBackupFile(file,hash):
        with open(file + ".sha256", "w") as f:
            f.write(hash)

    def createBackupTopicDir(dir):
        try:
            mkdir(dir)
        except FileExistsError:
            pass

    def currentMessageCountInBinFile(file):
        try:
            with open(file) as f:
                return sum(1 for _ in f)
        except:
            return 0

    def decodeMsgToUtf8(msg):
        try:
            return msg.value().decode('utf-8')
        except:
            print("decoding msg to utf-8 failed")
            return None

    def writeDataToKafkaBinFile(file,msg,mode):
        try:
            with open(file, mode) as f:
                f.write(msg)
                f.write("\n")
        except:
            print(f"unable to write to {file}")

    def createTarGz(dir,file):
        _file_tar_gz = dir + "/" + datetime.now().strftime("%Y%m%d-%H%M%S") + ".tar.gz"
        try:
            _t = tarfile.open(_file_tar_gz, "w:gz")
            _t.add(file)
            _t.close()
        except:
            print(f"unable to create tar.gz file of {file}")

        print(f"Created Successful Backupfile: {_file_tar_gz}")
        Common.createSha256OfBackupFile(_file_tar_gz,Common.calculateSha256(_file_tar_gz))
        print(f"Created Successful Backup sha256 file: {_file_tar_gz}.sha256")
