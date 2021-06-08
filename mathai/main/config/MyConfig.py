#coding=utf-8
import json,os
from collections import OrderedDict
from jproperties import Properties
import os

#linux开放环境
filename='/home/mathai/myproj/edu-back/src/main/resources/application.properties'
# filename='/home/math/projects/edu-back/application.properties'

# filename='/root/projects/edu-back/src/main/resources/application.properties'
#windows环境
#filename='D:\\projects\\edu-back\\src\\main\\resources\\application.properties'
#生存环境
# filename='/root/projects/edu-back/application.properties'


def mkdir(fname):
    if os.path.exists(fname)==False:
        os.mkdir(fname)
def defaultConfig():
    global filename
    with open(filename, 'rb') as config_file:
        configs = Properties()
        configs.load(config_file)

        d=OrderedDict()
        d['src_path']=configs.get('upload_path')[0]

        d['dst_path']=configs.get('spring.resources.static-locations')[0][5:]


        d['ip'],d['port'],d['dbname']=parsedbConfig(configs.get('spring.datasource.url')[0])

        d['username']=configs.get('spring.datasource.username')[0]
        d['password']=configs.get('spring.datasource.password')[0]

        d['question_count']=int(configs.get('question_count')[0])
        d['json_output']=configs.get('json_chapter')[0]

        d['generate_path']=configs.get('generate_path')[0]


        d['taskPath']=configs.get('jobPath')[0]
        d['decisonPath']=configs.get('decisonPath')[0]
        d['learnParamPath']=configs.get('learnParamPath')[0]

        mkdir(os.path.dirname(d['taskPath']))
        mkdir(d['taskPath'])
        mkdir(d['decisonPath'])
        mkdir(d['learnParamPath'])
        return d
#解析数据库地址IP，port ,dbname
def parsedbConfig(url):
    #jdbc:mysql://192.168.1.36:3306/smartagent?
    head='jdbc:mysql://'
    tail='/'
    index=url.index(head)
    eindex=url.index(tail,index+len(head))
    ip_port=url[index+len(head):eindex]
    ip,port=ip_port.split(':')

    index=eindex+1
    tail='?'
    eindex=url.index(tail,index+1)
    dbname=url[index:eindex]
    return ip,port,dbname