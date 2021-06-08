__author__ = 'mathai'

import json
import numpy as np
from mathai.main.config.MyConfig import defaultConfig


def half_power(M):
    U,S,V=np.linalg.svd(M)

    return U.dot( np.diag(S**0.5)).dot(U.T)

def normalize(x):
    return x/np.linalg.norm(x)

def randomSigma(martix_cov):
    """
    这个随机的方向应该是 z>0的，表示三个度都是【正相关】的
    :param martix_cov:协方差矩阵
    :return:z~normal(0,martix_cov),并且单位化
            sigma=sqrt(zT @ martix_cov @z)
    """

    while True:
        z=np.random.randn(martix_cov.shape[0])
        z=half_power(martix_cov).dot(z)
        z=normalize(z)
        if z[0]>=0 and z[1]>=0 and z[2]>=0:break
    return z,np.sqrt(martix_cov.dot(z).dot(z))

class ModelParam():
    def __init__(self):
        self.spuls=0.3
        self.tplus=0
        self.sminus=0.3
        self.tminus=0
        #使用 给定知识点，专题的概率
        self.w=0.6
        self.p=[0.3,0.5,0.2]

        self.totalPlus=0
        self.totalMinus=0
        self.totalPlus_good=0
        self.totalMinus_good=0

    def updateCountDistribution(self,alpha=0.8):
        '''
        调整 选题数量的概率分布self.p
        alpha>1表示  增加选择n=3的概率
        alpha<1     减小选择n=3的概率
        :param alpha:
        :return:
        '''
        self.p[2]*=alpha

        p2=self.p[1]
        p1=self.p[0]

        self.p[0]=(1-self.p[2])*p1/(p1+p2)
        self.p[1]=(1-self.p[2])*p2/(p1+p2)

    def sampleQuestionCount(self):
        return np.random.choice([1,2,3],1,p=self.p)[0]

    def load(self,filename,createIfNotExist=False):
        '''
        从filename中加载 model param.如果filename不存在，
        就使用默认的参数，
        :param filename:
        :param createIfNotExist:如果filename不存在，需不需要把【默认参数】保存到filename中
        :return:
        '''
        import os

        if os.path.exists(filename)==False:
            if createIfNotExist:
                self.save(filename)
                return True
            return False

        with(open(filename)) as fs:
            d=json.load(fs)

            self.spuls=d['splus']
            self.tplus=d['tplus']
            self.sminus=d['sminus']
            self.tminus=d['tminus']
            self.w=d['w']
            self.p=d['p']

            self.totalPlus=d['totalPlus']
            self.totalMinus=d['totalMinus']
            self.totalPlus_good=d['totalPlus_good']
            self.totalMinus_good=d['totalMinus_good']

        return True
    def save(self,filename):
        '''
        把model的参数 保存到filename中去
        :param filename:
        :return:
        '''
        with(open(filename,'w')) as fs:
            json.dump(self.getJson(),fs)

    def getJson(self):
        '''
        返回json，代表model param
        :return:
        '''
        d={}
        d['splus']=self.spuls
        d['tplus']=self.tplus
        d['sminus']=self.sminus
        d['tminus']=self.tminus
        d['w']=self.w
        d['p']=self.p

        d['totalPlus']=self.totalPlus
        d['totalMinus']=self.totalMinus
        d['totalPlus_good']=self.totalPlus_good
        d['totalMinus_good']=self.totalMinus_good
        return d
    def loadChapterData(self,filename):
        '''
        从文件 加载 到
        self.array_questions:array(n,3),n个题目,3度，但注意。我做了【数据清洗】
        self.dict_questionId_index：dict(str,index),问题id 与 self.array_questions 索引的映射关系。注意。我做了【数据清洗】
        self.dict_zhuantiId_questions:dict(str,list):专题下 所有问题的id，但注意。我【没做】了【数据清洗】
        self.dict_zsdId_questions::dict(str,list):知识点下 所有问题的id，但注意。我【没做】了【数据清洗】
        self.dict_questionId_questions：dict(str,dict):问题id 与问题json的对应关系。注意。我做了【数据清洗】
        :param filename: 目录文件夹
        :return:
        '''
        from collections import  defaultdict
        with(open(filename)) as fs:
            chapter=json.load(fs)[0]["children"]


            self.array_questions=[]
            self.dict_questionId_index=defaultdict(int)
            self.dict_zhuantiId_questions=defaultdict(list)
            self.dict_zsdId_questions=defaultdict(list)
            self.dict_questionId_questions=defaultdict(dict)

            tmp_zhuantiId_zhd={}
            stack=[]

            for child in chapter:
                stack.append((child,1))

            while len(stack)>0:
                context,level=stack.pop()
                if level==5:
                    nd,zhd,cxd=context['nd'],context['zhd'],context['cxd']
                    if nd<=1 and zhd<=1 and cxd<=1 and nd>0 and zhd>0 and cxd>0:
                        self.dict_questionId_index[context['id']]=len(self.array_questions)
                        self.array_questions.append([nd,zhd,cxd])
                        self.dict_questionId_questions[context['id']]=context
                    continue
                if level==3:
                    _zhuanId=context['id']
                    tmp_zhuantiId_zhd[_zhuanId]=context
                sub_tasks=context['children']

                for child in sub_tasks:
                    stack.append((child,level+1))
                    if level==4:
                        _zsdId=context['id']
                        self.dict_zsdId_questions[_zsdId].append(child['id'])

            for _zhuanId,_zhuanJson in  tmp_zhuantiId_zhd.items():
                zsds=_zhuanJson['children']
                for zsd in zsds:
                    _zsdId=zsd['id']
                    self.dict_zhuantiId_questions[_zhuanId].extend(self.dict_zsdId_questions[_zsdId])

            self.array_questions=np.array(self.array_questions)


    def choose_question(self,student_attr,target,zhuanIds=[],zsdIds=[],filter_question=set(),error_questions=[]):
        """
            从给定的【专题下 union 知识点】下 选择出可以达到【目标】的题目，并且返回这些题目的id

            算法实现：
                Q=专题下 和 知识点下 的题目
                Q=Q-filter_question

                z~eigVector
                ...
                ...

                由于s,t,z属性的原因，可能导致【无题可选】，这种情况下默认返回

        :param student_attr:学生的属性,array,(难度,综合度,创新度)
        :param target:+/-
        :param zhuanIds:list 专题的Id
        :param zsdIds:list   知识点的Id
        :param filter_question:set， 这些题目不进行选择
        :param error_questions:set， 错图本ID


        :return:dict
            "sigma":sigma,   当前选题的方差
            "chooseFromError":False, 是不是使用错题本
            "questionIds":list,选择的题目Ids,可以是[]

        """

        if isinstance(student_attr,list):student_attr=np.array(student_attr)

        n=self.sampleQuestionCount()
        #这里 做数据清洗
        Q=set([x for zhuanId in zhuanIds for x in self.dict_zhuantiId_questions[zhuanId] if x in self.dict_questionId_index])


        for zsdId in zsdIds:
            for x in self.dict_zsdId_questions[zsdId]:
                if x in self.dict_questionId_index:
                    Q.add(x)
        # 注意，这里过滤掉那些 做过的题目
        Q=list(Q-filter_question) #list of questionId


        array_question=np.array([self.array_questions[self.dict_questionId_index[questionId]] for questionId in Q])
        #或者array_question[i] 的questionId
        whichQuestion={i:Q[i] for i in range(len(Q))}
        M=np.cov(array_question,rowvar=False)

        direction,sigma=randomSigma(M)


        result={}

        u=student_attr.dot(direction)
        q=array_question.dot(direction)

        if target=='+':
            lower=u-self.tplus-self.spuls*sigma
            upper=u-self.tplus+self.spuls*sigma

        elif np.random.rand()<self.w or len(error_questions)==0:
            lower=u+self.tminus-self.sminus*sigma
            upper=u+self.tminus+self.sminus*sigma
        else:
            result=np.random.choice(error_questions,min(len(error_questions),n),False).tolist()
            return {
                "sigma":sigma,
                "chooseFromError":True,
                "questionIds":result
            }
        chioced_set=np.nonzero((q<=upper)*(q>=lower))[0]
        if len(chioced_set)==0:
            chioceIdx=np.argmin((q-u)**2)

            return {
                "sigma":sigma,
                "chooseFromError":False,
                "questionIds":[chioceIdx],
                "smallDistance":True
            }

        chioced_index=np.random.choice(chioced_set,min(len(chioced_set),n),False)
        result=[whichQuestion[ii] for ii in chioced_index]


        result={
            "sigma":sigma,
            "chooseFromError":False,
            "questionIds":result
        }
        return  result



    def feedBackForPlusTarget(self,isRight,sigma):
        """
        对+的反馈
               如果达标，  n 应该变小
                         选择范围splus应该变大，试图探索更多题目
            如果没有达标，  n 应该变大
                        tplus应该变大，让更多的【简单题目】被选择
            注意,t+变小 对应着 变难
                t+变大 对应着 变容易
                对t+做缩放表示 相对 当前水平
                对t+做平移表示 相对 整体水平(sigma)
        :param isRight:
        :param sigma:本次选题，题目的 标准差
        :return:
        """
        self.totalPlus+=1
        if isRight:#达到米标
            self.totalPlus_good+=1
            self.updateCountDistribution(0.9)
            self.spuls*=1.05
            self.tplus*=0.8*self.tplus  #适当增加难度,这里对t进行的是缩放操作，
        else:
            self.updateCountDistribution(1.1)
            self.tplus+=0.2*sigma #减小难度,这里对t做的是平移操作，以sigma为度量
    def feekBackForMinusTarget(self,isRight,sigma,chooseFromError=False):
        '''

        :param isRight:
        :param sigma:本次选题，题目的 标准差
        :param chooseFromError:是否是从错题本选择的
        注意,t-变小 对应着 变容易
            t-变大 对应着 变难
                对t-做缩放表示 相对 当前水平
                对t-做平移表示 相对 整体水平(sigma)

        :return:
        '''
        self.totalMinus+=1
        if isRight:#没有达到目标
            if chooseFromError:
                self.w=min(self.w+0.1,1)
                self.tminus+=0.1*sigma
            else:
                self.w=max(self.w-0.1,0.1)
                self.updateCountDistribution(1.1)
                self.tminus+=0.2*sigma #因为学生最对了，增大难度
        else:#达到了目标,学生出错了
            self.totalMinus_good+=1
            if chooseFromError:
                self.w=max(self.w-0.1,0.05)
            else:
                self.w=min(self.w+0.1,1)
                self.updateCountDistribution(0.9)
                self.sminus*=1.05
                self.tminus=self.tminus*0.8  #适当减小难度，因为学生被 “难住了”

if __name__ == '__main__':
    param=ModelParam()
    param.save('xx.json')
    config=defaultConfig()
    param.loadChapterData(config['json_output'])

    param.tminus=0.1
    param.w=0.5
    questionIds=param.choose_question([0.3,0.3,0.3],
                          '-',
                          ['26898a6c144411eb8932799142100f31'],
                          ['2689d8e6144411eb8932799142100f31','2a39ccb003e811eb9aaebd621c7eea23'],
                          error_questions=['ss','xx','kkk'])


    print(questionIds)