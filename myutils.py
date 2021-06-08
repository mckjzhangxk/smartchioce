__author__ = 'mathai'
import json
import numpy as np
from collections import defaultdict

array_questions = []
dict_questionId_index = defaultdict(int)
dict_zhuantiId_questions = defaultdict(list)
dict_zsdId_questions = defaultdict(list)
dict_questionId_questions = defaultdict(dict)


def normalize(x):
    return x/np.linalg.norm(x)

def randomSigma(martix_cov_half):
    """

    :param martix_cov:协方差矩阵
    :return:z~normal(0,martix_cov),并且单位化
            sigma=sqrt(zT @ martix_cov @z)
    """
    za=np.random.randn(martix_cov_half.shape[0])
    z=martix_cov_half.dot(za)
    z=normalize(z)*np.sign(z[0])

    return normalize(za),z,np.sqrt((martix_cov_half.dot(martix_cov_half)).dot(z).dot(z))

def loadChapterData(filename):
    with(open(filename)) as fs:
        chapter = json.load(fs)[0]["children"]

        global array_questions
        global dict_questionId_index
        global dict_zhuantiId_questions
        global dict_zsdId_questions
        global dict_questionId_questions

        tmp_zhuantiId_zhd = {}
        stack = []

        for child in chapter:
            stack.append((child, 1))

        while len(stack) > 0:
            context, level = stack.pop()
            if level == 5:
                dict_questionId_index[context['id']] = len(array_questions)
                array_questions.append([context['nd'], context['zhd'], context['cxd']])
                dict_questionId_questions[context['id']] = context
                continue
            if level == 3:
                _zhuanId = context['id']
                tmp_zhuantiId_zhd[_zhuanId] = context
            sub_tasks = context['children']

            for child in sub_tasks:
                stack.append((child, level + 1))
                if level == 4:
                    _zsdId = context['id']
                    dict_zsdId_questions[_zsdId].append(child['id'])

        for _zhuanId, _zhuanJson in tmp_zhuantiId_zhd.items():
            zsds = _zhuanJson['children']
            for zsd in zsds:
                _zsdId = zsd['id']
                dict_zhuantiId_questions[_zhuanId].extend(dict_zsdId_questions[_zsdId])

        array_questions = np.array(array_questions)


def half_power(M):
    U, S, V = np.linalg.svd(M)

    return U.dot(np.diag(S ** 0.5)).dot(U.T)


def getQuestionInZhuanTi(ztid):
    questionids = dict_zhuantiId_questions[ztid]
    questions = [dict_questionId_questions[q] for q in questionids]
    #
    # for q in questionids:
    # ss=array_questions[dict_questionId_index[q]]
    #     if(np.any(ss>=1)):
    #         print(q)
    question_array = [array_questions[dict_questionId_index[q]] for q in questionids if
                      np.all(array_questions[dict_questionId_index[q]] < 1)]

    return questions, np.array(question_array)


def listZhuanTi():
    for x in dict_zhuantiId_questions.keys():
        print(x)


def drawArrow(A, direction, ax,color,size):
    '''
    Draws arrow on specified axis from (x, y) to (x + dx, y + dy).
    Uses FancyArrow patch to construct the arrow.

    The resulting arrow is affected by the axes aspect ratio and limits.
    This may produce an arrow whose head is not square with its stem.
    To create an arrow whose head is square with its stem, use annotate() for example:
    Example:
        ax.annotate("", xy=(0.5, 0.5), xytext=(0, 0),
        arrowprops=dict(arrowstyle="->"))
    '''
    # fig = plt.figure()
    #     ax = fig.add_subplot(121)
    # fc: filling color
    # ec: edge color
    ax.arrow(A[0], A[1], direction[0], direction[1],
             length_includes_head=True,  # 增加的长度包含箭头部分
             head_width=size, head_length=size*2, fc='g', ec=color)
    # 注意： 默认显示范围[0,1][0,1],需要单独设置图形范围，以便显示箭头


def analysis(Q):
    u = np.mean(Q, axis=0)
    M = np.cov(Q, rowvar=False)
    sigma = half_power(M)

    U, S, V = np.linalg.svd(M)
    return u, sigma, U[:, 0], U[:, 1]


def distance_choose(u,Q,direction,sigma,s=0.5,t=0):


    upper=u.dot(direction)-t+s*sigma
    lower=u.dot(direction)-t-s*sigma
    q=Q.dot(direction)

    chioced_set=np.nonzero((q<=upper)*(q>=lower))[0]

    if len(chioced_set)==0:return None
    chioced_index=np.random.choice(chioced_set,1,False)[0]

    return Q[chioced_index]
loadChapterData('st.json')
# listZhuanTi()
# question,question_array=getQuestionInZhuanTi('9cef2eec2ded11eb99b887cbc3aefd92')
# analysis(question_array)
# print(len(question))
# print(question_array.shape)
