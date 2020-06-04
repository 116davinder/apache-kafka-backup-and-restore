from hashlib import sha256
from datetime import datetime
import os
import tarfile
import json
import logging

class Common:

    def setLoggingFormat():
        logging.basicConfig(
            format='{ "@timestamp": "%(asctime)s","level": "%(levelname)s","thread": "%(threadName)s","name": "%(name)s","message": "%(message)s" }'
        )
        logging.getLogger().setLevel(logging.INFO)

    def listFiles(dir):
        try:
            return os.listdir(dir)
        except:
            return []

    def readJsonConfig(file):
        try:
            with open(file) as cf:
                logging.info(f'loading {file} file')
                return json.load(cf)
        except json.decoder.JSONDecodeError as e:
            logging.error(f'{e}')
            exit(1)

    def calculateSha256(file):
        with open(file,"rb") as f:
            return sha256(f.read()).hexdigest();

    def createSha256OfBackupFile(file,hash):
        try:
            with open(file + ".sha256", "w") as f:
                f.write(hash)
        except:
            logging.error(f'unable to write to {file}.sha256')

    def createBackupTopicDir(dir):
        try:
            os.mkdir(dir)
        except FileExistsError as e:
            logging.info(e)
        except:
            logging.error(f'unable to create folder {dir}')

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
            logging.error(f'decoding msg to utf-8 failed')
            return None

    def writeDataToKafkaBinFile(file,msg,mode):
        try:
            with open(file, mode) as f:
                f.write(msg)
                f.write("\n")
        except:
            logging.error(f'unable to write to {file}')

    def createTarGz(dir,file):
        _date = datetime.now().strftime("%Y%m%d-%H%M%S")
        _file_tar_gz = os.path.join(dir, _date ) + ".tar.gz"
        try:
            _t = tarfile.open(_file_tar_gz, "w:gz")
            _t.add(file,arcname=_date + ".bin")
            _t.close()
        except:
            logging.error(f'unable to create/write to {_file_tar_gz}')

        logging.info(f"Created Successful Backupfile {_file_tar_gz}")
        Common.createSha256OfBackupFile(_file_tar_gz,Common.calculateSha256(_file_tar_gz))
        logging.info(f"Created Successful Backup sha256 file of {_file_tar_gz}.sha256")

    def isSha256HashMatched(file, hashfile):
        try:
            with open(hashfile) as f:
                file_hash = f.readline().strip()
                if Common.calculateSha256(file) == file_hash:
                    return True
        except FileNotFoundError as e:
            logging.error(e)
        
        return False

    def openTarFile(file,extractDir):
        _sname = os.path.basename(file).split(".")[0] + ".bin"
        try:
            os.remove(os.path.join(extractDir,_sname))
        except FileNotFoundError:
            pass

        try:
            _et = tarfile.open(file)
            _et.extract(_sname, extractDir)
            return True
        except FileNotFoundError as e:
            logging.error(e)

        return False