import json

from django.http import HttpResponse

from mathai.main.algorithm import genPushment,smartChooseQuestionFromZsd
from mathai.main.config import defaultConfig
from mathai.main.mydb import DBManager
import mathai.main.question.parseWordDocument as questionService
from  mathai.main.algorithm.pushTask import createNewJob,feedback,executeTasks,cancleStudentTask
# Create your views here.


config=defaultConfig()

def createPushment(request):
    '''

    :param studentId: 学生ID
    :param config: 使用到config.question_count，返回的数组大小
    :param config: dbm 数据库对象

    :return: dict

    必备字段
    success:True or False

    success:True
        questionIds:list of question
    success:False
        msg:错误信息
    '''
    dbm = DBManager(config)
    body=json.loads(request.body.decode())
    question=genPushment(body['studentId'],config,dbm)

    if len(question)>0:
        success={'success':True,'questionIds':question}
    else:
        success = {'success': False, 'msg':'所选知识点下没有题目可以生成'}
    return HttpResponse(json.dumps(success,ensure_ascii=False,indent=2))

def smartChiose(request):
    dbm = DBManager(config)
    body=json.loads(request.body.decode())
    questionIds=smartChooseQuestionFromZsd(body['studentId'],body['zsdIds'],config,dbm)
    if(len(questionIds)>0):
        success={'success':True,"count":len(questionIds),'questionIds':questionIds}
    else:
        success={'success':False,"msg":"所选知识点下没有题目可以生成"}
    return HttpResponse(json.dumps(success,ensure_ascii=False,indent=2))


def inputQuestions(request):
    result=questionService.service(config)
    return HttpResponse(json.dumps(result,ensure_ascii=False,indent=2))



def createStudentAutoPushmentJob(request):
    '''
    为一个学生创建定期推送的任务.
    studentId
    pattern
    peridic
    pushData

    :param request:
    :return:
    '''
    field=['studentId','pattern','peridic','pushDate']
    try:
        dbm = DBManager(config)
        jsonData=json.loads(request.body.decode())

        isOK=True
        for f in field:
            if f not in jsonData:
                success={'success':False,'message':'缺少字段'+f}
                isOK=False
                break
        if isOK:
            createNewJob(jsonData,config,dbm)
            success={'success':True}
    except Exception as e:
        success={'success':False,"message":str(e)}
    return HttpResponse(json.dumps(success,ensure_ascii=False,indent=2))

def feedBackFromStudent(request):
    '''
    学生做完题目后反馈给系统，系统对 自身进行调整，以实现更加智能

    studentId
    isRight
    hwId


    :param request:
    :return:
    '''
    field=['studentId','isRight','hwId']
    try:
        jsonData=json.loads(request.body.decode())

        isOK=True
        for f in field:
            if f not in jsonData:
                success={'success':False,'message':'缺少字段'+f}
                isOK=False
                break
        if isOK:
            feedback(jsonData,config)
            success={'success':True}
    except Exception as e:
        success={'success':False,"message":str(e)}
    return HttpResponse(json.dumps(success,ensure_ascii=False,indent=2))


def cancleTask(request):
    field=['studentId']
    try:
        jsonData=json.loads(request.body.decode())

        isOK=True
        for f in field:
            if f not in jsonData:
                success={'success':False,'message':'缺少字段'+f}
                isOK=False
                break
        if isOK:
            dbm = DBManager(config)
            cancleStudentTask(jsonData['studentId'],config,dbm)
            success={'success':True}
    except Exception as e:
        success={'success':False,"message":str(e)}
    return HttpResponse(json.dumps(success,ensure_ascii=False,indent=2))

def runEveryDayTask():
    dbm=DBManager(config)
    executeTasks(config,dbm)
def testCron():
    import datetime
    with open('/home/mathai/myproj/smartchioce/test.txt','w') as fs:
        fs.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%s'))
    print('cron work')
