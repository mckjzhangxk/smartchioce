from collections import  defaultdict

import numpy as np

from mathai.main.mydb.DBUtils import DBManager
from mathai.main.config.MyConfig import defaultConfig

'''
u:(difficult,complex,creative)
delta:(difficult,complex,creative)的浮动
Q：（M，3）的题目

返回Q中被选中的题目序号
'''
def smartchoose(u,Q,K):
    Qcopy=np.copy(Q)
    def check(iis):
        qs=Qcopy[iis]
        qs_mean=qs.mean(axis=0)
        print('mean:',qs_mean)
        print('std:',np.std(qs,axis=0))

    K=min(K,Q.shape[0])
    delta=np.std(Q,axis=0)
    s=np.clip(np.random.randn(K,Q.shape[1])*delta+u,0,1)

    queue=[]

    for k in range(K):
        M=((Q-s[k])**2).sum(axis=1)
        selected=np.argmin(M)
        queue.append(selected)
        Q[selected][0]=float('inf')
    # check(queue)
    return queue

#数据库的字段转成矩阵的列
def tuple2array(qs):
    arr=[]
    for q in qs:
        arr.append([q[4],q[5],q[6]])
    return np.array(arr)
#综合老师，家长，学生得出的平均指标(均值+方差)
def attr2array(attr):
    attr=np.array(attr).reshape((1,3))
    return attr


def sortQuestionByOrder(questions):
    '''

        :param questions,sql查询出来的问题集合
        :return:list（tuple）,每一个元素表示一个类型的题目集合

        索引表:tuple[0]=list of index: 每个题目在questions的索引
        题目表:tuple[1]=question array:numpy array=(#questoins,3)
    '''
    mydict=defaultdict(list)
    for i,q in enumerate(questions):
        mydict[q[3]].append((i,q))

    ret=[]
    for (k,qlist) in mydict.items():
        indexes=[q[0] for q in qlist]
        qs     =[q[1] for q in qlist]

        #list question => array_question
        questions_array=tuple2array(qs)
        ret.append((indexes,questions_array))
    return ret

def genPushment(studentId,config,dbm):
    '''
    智能推送的方法

    1.选择老师 和 学生 设置的【知识点】下面的【题目】，并且这些【题目】没有被推送过，这些题目的集合叫做 Q。
    2.通过匹配算法，对Q进行排序，最匹配的排在最前面
    3.返回头config['question_count']个 匹配的ID

    :param studentId: 学生ID
    :param config: 使用到config.question_count，返回的数组大小
    :param config: dbm 数据库对象

    :return: list of questionId，size=config.question_count

    '''
    sql="SELECT uid,title,url,catalog,difficult,complex,creative,remark,answer from question where catalog in (select DISTINCT zsdid from studentplan where studentid='%s') and uid not in (select distinct questionid from pushment  where studentid='%s');"%(studentId,studentId)

    questions=dbm.select(sql)
    if(len(questions)==0):
        return []
    list_of_types=sortQuestionByOrder(questions)

    #学生属性查询
    sql="select tdifficult,tcomplex,tcreative from studentattr where userid='%s';"%studentId
    studentAttr=dbm.select(sql)[0]
    u=attr2array(studentAttr)

    chioces_question=[]
    for (index_table,questions_array) in list_of_types:
        chioces=smartchoose(u,questions_array,config['question_count'])
        for c in chioces:
            chioces_question.append(questions[index_table[c]][0])

    return chioces_question
'''
为studentId在zsdIds的知识度下选择题目，返回题目的ids[]
zsdIds:[],保存所有的知识度id
config.question_count/2是题目的数量
dbm:数据库对象
'''
def smartChooseQuestionFromZsd(studentId,zsdIds,config,dbm):
    if len(zsdIds)==0:return []
    zsdIds=["'"+x+"'" for x in zsdIds]
    ids=",".join(zsdIds)
    sql="select uid,title,url,catalog,difficult,complex,creative,remark,answer  from question where catalog in (%s)"%ids
    questions=dbm.select(sql)
    if(len(questions)==0):
        return []
    questions_array=tuple2array(questions)

    sql="select creative,complex,difficult from studentattr where userid='%s';"%studentId
    studentAttr=dbm.select(sql)[0]
    # u,sigma=attr2array(studentAttr)
    u=np.float32([studentAttr[0],studentAttr[1],studentAttr[2]])
    chioces=smartchoose(u,questions_array,config['question_count'])

    chioces_question=[questions[c][0] for c in chioces]
    return chioces_question

if __name__ == '__main__':
    config=defaultConfig()
    dbm=DBManager(config)
    # genPushment('1897290','2020-06-18',config,dbm)
    xx=smartChooseQuestionFromZsd('1897290',['fc22ba14b0fe11eaadfd4cebbd70918b'],config,dbm)
    print(xx)