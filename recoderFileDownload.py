#!F:\software\python36\python3.exe
#kongz 下载文件
import paramiko
import threading
import json
import os
import sys
from stat import S_ISDIR as isdir
import logging
import zipfile
import time

#建立连接，获取sftp句柄
def sftp_connect(username,password,host,port):
    global logger
    client = None
    sftp = None
    try:
        client = paramiko.Transport((host,port))
    except Exception as error:
        logger.error(error)
    else:
        try:
            client.connect(username=username, password=password)
        except Exception as error:
            logger.error(error)
        else:
            sftp = paramiko.SFTPClient.from_transport(client)
    return client,sftp
#断开连接
def disconnect(client):
    global logger
    try:
        client.close()
    except Exception as error:
        logger.error(error)

def check_local(localPath):
    global logger
    if not os.path.exists(localPath):
        try:
            os.mkdir(localPath)
        except IOError as err:
            logger.error(err)

#下载方法
def downLoad(client, sftp, remote, local):
    global logger
    #检查远程文件
    try:
        result = sftp.stat(remote)
    except IOError as err:
        error = '[ERROR %s] %s: %s' %(err.errno,os.path.basename(os.path.normpath(remote)),err.strerror)
        logger.error(error)
    else:
        if isdir(result.st_mode):
            dirname = os.path.basename(os.path.normpath(remote))
            local = os.path.join(local, dirname)
            #local = local.replace("\\","/")
            check_local(local)
            for file in sftp.listdir(remote):
                sub_remote = os.path.join(remote, file)
                sub_remote = sub_remote.replace("\\","/")
                downLoad(client, sftp,sub_remote,local)
        else:
            if os.path.isdir(local):
                local = os.path.join(local, os.path.basename(remote))
            try:
                sftp.get(remote, local)
            except IOError as err:
                logger.error(err)
            else:
                logger.info('[get] %s %s %s', remote, '==>', local)
                lock.acquire()
                global finish
                finish += 1
                lock.release()
                logger.info('已下载 [%d] 个文件', finish)

#压缩文件
def writeAllFileToZip(absDir,zipFile):
    global logger
    for f in os.listdir(absDir):
        absFile=os.path.join(absDir,f) #子文件的绝对路径
        if os.path.isdir(absFile): #判断是文件夹，继续深度读取。
            zipFile.write(absFile) #在zip文件中创建文件夹
            logger.info('写入 %s 到压缩包 %s 成功', absFile, zipFile.filename)
            writeAllFileToZip(absFile,zipFile) #递归操作
        else: #判断是普通文件，直接写到zip文件中。
            zipFile.write(absFile)
            logger.info('写入 %s 到压缩包 %s 成功', absFile, zipFile.filename)
    return

if __name__ == "__main__":
    #日志
    logging.basicConfig(level=logging.INFO,format ='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()
    logFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler("log.txt")
    handler.setLevel(logging.INFO)
    handler.setFormatter(logFormatter)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logFormatter)
    logger.addHandler(handler)
    #logger.addHandler(console)
    #锁
    lock = threading.Lock()
    #条件
    finish = 0
    #读取配置文件
    configFile = open('config.json')
    configs = json.loads(configFile.read())
    configFile.close()
    
    logger.info('工作目录： %s', configs['workDir'])
    #检查本地工作目录（父目录）
    check_local(configs['workDir'])
    threadList = []
    for config in configs['threads']:
        logger.info("=======================配置信息 start=============================")
        logger.info("HostAddress %s",config['HostAddress'])
        logger.info('Port %s', config['Port'])
        logger.info('Username %s',config['Username'])
        logger.info('Password %s',config['Password'])
        logger.info('RemotePath %s',config['RemotePath'])
        logger.info('LocalPath %s',config['LocalPath'])
        logger.info("=======================配置信息 end=============================")
        client,sftp = sftp_connect(config['Username'],config['Password'],config['HostAddress'],config['Port'])
        #创建本地目录
        check_local(config['LocalPath'])
        #多线程
        t = threading.Thread(target=downLoad, args=(client, sftp, config['RemotePath'], config['LocalPath']))
        t.start()
        threadList.append(t)
        #单线程
        #downLoad(client, sftp, config['RemotePath'], config['LocalPath'])
    for t in threadList:
        t.join()

    #压缩
    # while threading.active_count() == 1:
    logger.info('=======================准备开始压缩==========================')
    #time.sleep(3)
    logger.info('==========================开始压缩。。。==========================')
    check_local(configs['zipDir'])
    zipFilePath = os.path.join(configs['zipDir'], configs['zipName'] + '.zip')
    zipFile = zipfile.ZipFile(zipFilePath, 'w', zipfile.ZIP_DEFLATED, allowZip64=True)
    absZipFileDir = configs['workDir']
    writeAllFileToZip(absZipFileDir, zipFile)
    logger.info('==========================压缩完成==========================')
    #保留终端
    print("Press Enter to continue ...")
    input()