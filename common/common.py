from hashlib import sha256
from datetime import datetime
import os
import tarfile
import json
import logging
import pathlib

def setLoggingFormat(level=20):
    logging.basicConfig(
        format='{ "@timestamp": "%(asctime)s","level": "%(levelname)s","thread": "%(threadName)s","name": "%(name)s","message": "%(message)s" }'
    )
    logging.getLogger().setLevel(level)

def listDirs(dir):
    try:
        return sorted(os.listdir(dir))
    except FileNotFoundError as e:
        logging.error(e)
    
    return []

def findFilesInFolder(dir,pattern="*"):
    _list = []
    result = list(pathlib.Path(dir).rglob(pattern))
    for path in result:
        if os.path.isfile(path):
            _list.append(path)
    return _list

def readJsonConfig(file):
    try:
        with open(file) as cf:
            logging.debug(f'loading {file} file')
            return json.load(cf)
    except json.decoder.JSONDecodeError as e:
        logging.error(f'{e}')
        exit(1)

def calculateSha256(file):
    try:
        with open(file,"rb") as f:
            return sha256(f.read()).hexdigest();
    except FileNotFoundError as e:
        logging.error(e)
    return None

def createSha256OfBackupFile(file,hash):
    try:
        with open(file + ".sha256", "w") as f:
            f.write(hash)
    except:
        logging.error(f'unable to write to {file}.sha256')

# def currentMessageCountInBinFile(file):
#     try:
#         with open(file) as f:
#             return sum(1 for _ in f)
#     except FileNotFoundError as e:
#         logging.error(e)
    
#     return 0

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
    _hash = calculateSha256(_file_tar_gz)
    if _hash is not None:
        createSha256OfBackupFile(_file_tar_gz,_hash)
        logging.info(f"Created Successful Backup sha256 file of {_file_tar_gz}.sha256")

def isSha256HashMatched(file, hashfile):
    try:
        with open(hashfile) as f:
            file_hash = f.readline().strip()
            if calculateSha256(file) == file_hash:
                return True
    except FileNotFoundError as e:
        logging.error(e)
    
    return False

def extractBinFile(file,hashfile,extractDir):
    
    if isSha256HashMatched(file,hashfile):
        _sname = os.path.basename(file).split(".")[0] + ".bin"
        try:
            _et = tarfile.open(file)
            _et.extract(_sname, extractDir)
            try:    
                os.remove(file)
                os.remove(hashfile)
            except FileNotFoundError:
                pass

            return os.path.join(extractDir,_sname)
        except FileNotFoundError as e:
            logging.error(e)
    return None

def findNumberOfPartitionsInTopic(list):
    _lp = []
    for i in list:
        _lp.append(i)
    return _lp