__author__ = 'mathai'

import json
import os
from  mathai.main.algorithm.autoPushment import ModelParam
import datetime
import random
import numpy as np
import uuid
from mathai.main.config.MyConfig import defaultConfig

from mathai.main.mydb.DBUtils import DBManager


def easy_str2date(s):
    return datetime.datetime.strptime(s, '%Y-%m-%d')


def easy_data2str(d):
    return d.strftime('%Y-%m-%d')


def getStudentAttr(studentId, dbm):
    '''

    :param studentId:
    :param dbm:
    :return:array(1x3),学生当前的属性,没有找到返回None
    '''

    sql = "select t.difficult,t.complex,t.creative from studentattr t where t.userid='%s'" % studentId

    student_attr = dbm.select(sql)

    if len(student_attr) == 0: return None

    attr = np.array(student_attr[0])

    return attr


def getStudentTestZhuanTiAndZsd(studentId, dbm):
    '''

    :param studentId:
    :param dbm:
    :return: list:zhuantiIds,为学生选择的[专题]IDs
            list:zsdIds,为学生选择的[知识点]IDs
    '''
    sql = "select DISTINCT zsdid from studentplan where studentid='%s'" % studentId
    zsdIds = dbm.select(sql)
    zsdIds = [q[0] for q in zsdIds if q[0] is not None]

    sql = "select DISTINCT zhuantiid from studentplan where studentid='%s'" % studentId
    zhuantiIds = dbm.select(sql)
    zhuantiIds = [q[0] for q in zhuantiIds if q[0] is not None]

    return (zhuantiIds, zsdIds)


def getStudentFinishQuestionIds(studentId, dbm):
    '''
    查询之前推送过的题目id
    :param studentId:
    :param dbm:
    :return:set,学生做过的题目的questionid
    '''

    sql = "SELECT distinct questionid FROM pushment t where studentid='%s'" % studentId

    questionIds = dbm.select(sql)
    questionIds = [q[0] for q in questionIds if q[0] is not None]
    return set(questionIds)


def getStudentErrorQuestionIds(studentId, dbm):
    '''

    :param studentId:
    :param dbm:
    :return:list,学生错过的题目的questionid
    '''
    sql = "SELECT distinct questionid FROM errorquestion t where userid='%s'" % studentId

    questionIds = dbm.select(sql)
    questionIds = [q[0] for q in questionIds]
    return questionIds


def getStudentIdFromTaskList(dbm):
    '''
    从数据库获得那些需要执行定时任务的学生
    :param dbm:
    :return:
    '''
    sql = "select studentid from dailyjob where valid='T'"
    studentIds = dbm.select(sql)
    studentIds = [x[0] for x in studentIds]

    return studentIds


def insertPushment(studentId, dbm, questionIds):
    '''
    把questionIds 输入保存成一次推送

    字段：
        uid,studentId,questionId
        stime: eg 2020-12-22_30
        currentType:eg B
    注意 hwId=stime_currentType
    :param studentId:
    :param dbm:
    :param questionIds:
    :return:
    '''
    queryTime = easy_data2str(datetime.datetime.now())

    sql = "SELECT questionid,type FROM pushment a WHERE a.studentid='%s' AND a.stime like '%s%%'  order by stime,type" % (
    studentId, queryTime)

    select = dbm.select(sql)

    stime = queryTime + "_" + str(len(select))

    types = set([p[1] for p in select])

    currentType = chr(ord('A') + len(types))

    sqls = []

    for questionId in questionIds:
        sql = "insert into pushment(uid,studentId,stime,questionId,type,valid) values  ('%s','%s','%s','%s','%s','T')" % (
            str(uuid.uuid1()).replace('-', ''),
            studentId,
            stime,
            questionId,
            currentType,
        )
        sqls.append(sql)

    dbm.insert(sqls)

    return stime + '_' + currentType


def insertNewTask(studentId, pattern, peridic, pushdate, dbm):
    '''
    把一次创建记录在数据库中，设置这最后一次的有效，这样，数据库就有了
    对模式选择的历史记录。
    :param studentId:
    :param pattern: 模式序列 +-
    :param peridic: 模式周期
    :param pushdate: 本模式开始推送日期
    :param dbm:
    :return:
    '''
    sql = "update dailyjob set valid='F' where studentid='%s'" % studentId
    dbm.insert([sql])

    sql = "insert into dailyjob(uid,studentid,pattern,peridic,startdate,valid) values('%s','%s','%s','%d','%s','T')" % (
        str(uuid.uuid1()).replace('-', ''),
        studentId,
        pattern,
        peridic,
        pushdate
    )
    dbm.insert([sql])


def cancleStudentTask(studentId, config, dbm):
    sql = "update dailyjob set valid='F' where studentid='%s'" % studentId
    dbm.insert([sql])

    job = Task(studentId, config)
    job.deleteTask()


class Task():
    def __init__(self, studentId, config):
        '''
        一个Task针对一个学生
        :param studentId:
        :param config:
        :return:
        '''
        self.studentId = studentId
        self.student_machine_json = self.studentId + '.json'

        # 记录 推送模式，当前模式，推送时间
        self.taskPath = config['taskPath']
        #记录根据什么 做的推送决定
        self.decisonPath = config['decisonPath']
        #记录 model param
        self.learnParamPath = config['learnParamPath']

        self.config = config

    def createNewTask(self, pattern, peridic, pushment_date):
        '''
        在self.taskPath 目录下 建立关于学生的【推送计划json】
        :param pattern: eg ++-
        :param peridic: 推送的周期,间隔大约多长时间推送一次
        :param pushment_date:那一天执行这个推送任务
        :return:
        '''
        d = {}
        d['pattern'] = pattern
        d['peridic'] = peridic
        d['current'] = 0
        d['pushment_date'] = pushment_date

        with open(os.path.join(self.taskPath, self.student_machine_json), 'w') as fs:
            json.dump(d, fs)

        return d

    def deleteTask(self):
        '''
        删除self.taskPath下 学生的【推送计划json】
        :return:
        '''
        filepath = os.path.join(self.taskPath, self.student_machine_json)
        if os.path.exists(filepath):
            os.remove(filepath)

    def executeTask(self, dbm):
        '''
        执行一个job,我会把当前日期与pushment_date对比，只有到了当前日期(或在早于当前时间)，才会推送
            job={
                pattern：模式字符串++-
                current：当前的模式索引0,1,2....
                pushment_date：执行本job的日期
                peridic:下次推送 等peridic天
            }


        :return:
        '''

        job_json = None

        with open(os.path.join(self.taskPath, self.student_machine_json), 'r') as fs:
            job_json = json.load(fs)

            pattern, current = job_json['pattern'], job_json['current']
            str_pushment_date, peridic = job_json['pushment_date'], job_json['peridic']

            str_now = easy_data2str(datetime.datetime.now())

            # 将来的推送，不执行
            if (easy_str2date(str_now) < easy_str2date(str_pushment_date)): return

            target = pattern[current % len(pattern)]

            machile_model = ModelParam()

            machile_model.load(os.path.join(self.learnParamPath, self.student_machine_json), True)
            machile_model.loadChapterData(self.config['json_output'])



            # 数据准备 student_attr,target,zhuanIds=[],zsdIds=[]
            student_attr = getStudentAttr(self.studentId, dbm)
            if student_attr is None:
                return {"success": False,
                        "message": "user id：%s,not exist" % self.studentId,
                        "isEmpty": False}

            zhuanIds, zsdIds = getStudentTestZhuanTiAndZsd(self.studentId, dbm)

            if len(zhuanIds) == 0 and len(zsdIds) == 0:
                return {"success": False,
                        "message": "no question to do",
                        "isEmpty": True}

            errQuestionIds = getStudentErrorQuestionIds(self.studentId, dbm)
            filterQuestionIds = getStudentFinishQuestionIds(self.studentId, dbm)

            #多次选择，避免 题荒
            for i in range(3):
                chioce_result = machile_model.choose_question(student_attr, target, zhuanIds, zsdIds, filterQuestionIds,
                                                              errQuestionIds)
                if len(chioce_result['questionIds']) > 0: break

            #添加 推送到数据库
            if len(chioce_result['questionIds']) == 0:
                return {"success": False,
                        "message": "no question to do",
                        "isEmpty": True}

            hwId = insertPushment(self.studentId, dbm, chioce_result['questionIds'])

            #产生中间结果，这些中间结果 表示 基于 什么 机器做的决定

            #学生属性，机器参数,
            #目标(+/-)，当前选题范围(zsdIds,zhuanIds),sigma(当前选题的标准差)
            # 选择哪些题目.题目是否来自错题本
            #当前日期
            machile_decision = {}

            machile_decision['hwId'] = hwId
            machile_decision['user_attr'] = list(student_attr)
            machile_decision['machine'] = machile_model.getJson()

            machile_decision['target'] = target
            machile_decision['zsdIds'] = zsdIds
            machile_decision['zhuanIds'] = zhuanIds
            for k in chioce_result:
                machile_decision[k] = chioce_result[k]
            machile_decision['date'] = str_now

            self._dumpJson(machile_decision, os.path.join(self.decisonPath, self.student_machine_json), mode='a')


            #更新 下一个目标，下次推送时间
            str_pushment_date = easy_data2str(
                easy_str2date(str_now)
                + datetime.timedelta(random.choice(list(range(1, peridic + 1))))
            )

            job_json['current'] = current + 1
            job_json['pushment_date'] = str_pushment_date

        self._dumpJson(job_json, os.path.join(self.taskPath, self.studentId + '.json'))
        return {"success": True,
                "message": "",
                "isEmpty": False}

    def _dumpJson(self, obj, filename, mode='w'):
        '''
        把obj 直接写道filename 或者 追加到 filename
        追加的时候，filename保存的是一个list of json
        :param obj:json
        :param filename:
        :param mode:
        :return:
        '''
        if mode == 'w':
            with open(filename, 'w') as fs:
                json.dump(obj, fs)
        elif mode == 'a':
            if os.path.exists(filename):
                with open(filename, 'r') as fs:
                    current = json.load(fs) #current.type=list
                    current.append(obj)
                    obj = current
            else:
                obj = [obj]
            with open(filename, 'w') as fs:
                json.dump(obj, fs)


def executeTasks(config, dbm):
    '''
    crontab的定时任务！！！

        为studentIds的学生们执行定时任务
    :param config:
    :param dbm:
    :param studentIds:
    :return:
    '''
    result = []
    studentIds = getStudentIdFromTaskList(dbm)
    for studentId in studentIds:
        job = Task(studentId, config)
        job_result = job.executeTask(dbm)
        result.append((studentId, job_result))
    return result


def createNewJob(jsonData, config, dbm):
    '''
    启动对【学生】的新的推送模式，这个数据同时记录在
    【文件系统】和【数据库】

    【文件系统】对应这以后具体的执行,
    【数据库】 用于查询历史模式使用
    :param jsonData: studentId,pattern,pushDate,peridic
    :param config:
    :param dbm:
    :return:
    '''

    studentId, pattern, pushDate, peridic = jsonData['studentId'], jsonData['pattern'], jsonData['pushDate'], int(
        jsonData['peridic'])
    insertNewTask(studentId, pattern, peridic, pushDate, dbm)

    job = Task(studentId, config)
    return job.createNewTask(pattern, peridic, pushDate)


def feedback(jsonData, config):
    '''
    对机器选题的一次反馈，程序会判断 【这次测试是否 出自于 机器的选题】，
    如果是，根据反馈的结果，更新 【机器的参数】
    :param jsonData:反馈只需要告诉程序那个[学生]的那个[作业ID]，[是否正确]就可以
                studentId
                isRight
                hwId

    :param config:
            decisonPath:用于查询决策 参数，用于判断【测试是否是机器选题】
            learnParamPath:更新前后的大脑参数
    :return:
    '''
    studentId, isRight,hwId = jsonData['studentId'], jsonData['isRight'],jsonData['hwId']


    def findDecision():
        decision_file = os.path.join(config['decisonPath'], studentId + '.json')

        if os.path.exists(decision_file) == False: return None
        with open(decision_file) as fs:
            decisions = json.load(fs)

            for d in decisions:
                if d['hwId'] == hwId:
                    return d
        return None

    model = ModelParam()
    decision = findDecision()
    if decision is None: return

    learned_file_name = os.path.join(config['learnParamPath'], studentId + '.json')
    if model.load(learned_file_name):
        if decision['target'] == '+':
            model.feedBackForPlusTarget(isRight, sigma=decision['sigma'])
        else:
            model.feekBackForMinusTarget(isRight, sigma=decision['sigma'], chooseFromError=decision['chooseFromError'])
        model.save(learned_file_name)


if __name__ == '__main__':
    # config=defaultConfig()
    # dbm=DBManager(config)
    # print(getStudentAttr('1897290',dbm))
    #
    # print(getStudentFinishQuestionIds('1897290',dbm))
    #
    # print(len(getStudentFinishQuestionIds('1897290',dbm)))
    #
    #
    #
    # print(getStudentErrorQuestionIds('1897290',dbm))
    #
    # print(len(getStudentErrorQuestionIds('1897290',dbm)))
    #
    #
    # print(getStudentTestZhuanTiAndZsd('1897290',dbm))
    #
    #
    # insertPushment('1897290',dbm,[])

    ##########12-10 测试创建任务=======================
    # config=defaultConfig()
    # dbm=DBManager(config)
    # createNewJob(
    # {
    #         'studentId':'1897290',
    #         'pattern':'+-',
    #         'peridic':'2',
    #         'pushDate':'2020-12-7'
    #     }
    #     ,config,dbm)
    #
    #
    # createNewJob(
    #     {
    #         'studentId':'3682329',
    #         'pattern':'+--',
    #         'peridic':'1',
    #         'pushDate':'2020-12-10'
    #     }
    #     ,config,dbm)
    ##############################################################


    ##########12-10 测试执行定时任务=======================
    config=defaultConfig()
    dbm=DBManager(config)
    executeTasks(config,dbm)

    ##########12-10 测试反馈的正确性=======================

    # config=defaultConfig()
    # dbm=DBManager(config)
    #
    # feed_json={
    #     'studentId':'1897290',
    #     'isRight':True,
    #     'hwId':'2020-12-10_0_A'
    # }
    #
    # feedback(feed_json,config)

    #####################12-29测试取消任务####################################


    # config = defaultConfig()
    # dbm = DBManager(config)
    # cancleStudentTask('1897290', config, dbm)


    # config = defaultConfig()
    # dbm = DBManager(config)
    # executeTasks(config,dbm)
