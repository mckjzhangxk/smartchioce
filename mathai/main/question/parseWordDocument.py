#coding=utf-8
import os
import shutil
import json
import uuid
import codecs

from  mathai.main.question.dbUtils import insert_file_rec


def readDoc(filename):
    '''
    读取整个html内容返回
    :param filename: 
    :return:
    1.文件的内容 
    2.“”，如果文件不存在
    '''
    if os.path.exists(filename) == False:
        return ""
    with codecs.open (filename, "r",'gbk') as myfile:
        data=myfile.readlines()
        return "".join(data)

def findIndex(s,startTag,endTag):
    '''
    从s中查找startTag,endTag的索引返回，startTag必须出现在endTag之前
    

    Parameters
        ----------
        s:查询的字符串
        startTag:第一个标签
        endTag:第二个标签
    Returns
        ----------
            1.找不到startTag 返回（-1,-1）
            2.找到startTag,找不到endTag,返回（*,-1）
            3.找到后，返回（sinx,einx）
    
            sinx:startTag的第一个字符在s出现的索引
            einx:  endTag的第一个字符在s[len(startTag):]出现的索引
    '''

    startIndex=s.find(startTag)
    endIndex=-1
    if startIndex>=0:
        endIndex=s.find(endTag,startIndex+len(startTag))
    return (startIndex,endIndex)

def findContent(s,startTag,endTag):
    '''    
    在s中提取在startTag,endTag标签之间的内容返回
    
    :param s:查询的字符串
    :param startTag: 第一个标签
    :param endTag: 第二个标签
    :return: 
        1.如果找不到在2个标签之间的内容，返回“”
        2.startTag,endTag标签之间的内容返回，包含startTag，endTag
        eg: s=abc<h1>hello world</h1>body
            startTag=<h1>,endTag=</h1>
            return =<h1>hello world</h1>
    '''
    startIndex,endIndex=findIndex(s,startTag,endTag)

    if startIndex>=0 and endIndex>=0:
        head=s[startIndex:endIndex+len(endTag)]
        return head
    else:
        return ""


def findHtmlBody(s):
    '''
    找到html的body内容，包括<body>标签
    
    :param s: html code
    :return: 
        1.如果包含<body>...</body> 返回<body>...</body>
        2.否则返回”“
    '''
    startTag='<body'
    endTag='</body>'
    return findContent(s,startTag,endTag)

def findHtmlHead(s):
    '''
    找到html的head内容，包括<head>标签

    :param s: html code
    :return: 
        1.如果包含<head>...</head> 返回<head>...</head>
        2.否则返回”“
    '''
    startTag='<head'
    endTag='</head>'
    return findContent(s,startTag,endTag)

def removeTag(s):
    '''
    删除s中出现的所以< >对
    :param s:要进行剔除的字符串
    :return: 
        eg s=<style color=''><b>abc</b></style>
        return=abc
    '''
    if s==None:return ""
    while True:
        a=s.find("<")
        if a>=0:
            b=s.find(">",a)
            s=s[:a]+s[b+1:]
        else:
            break
    return s
def removeSpanTag(s):
    '''
    删除s中的 span 标签
    :param s:
    :return:
        eg s=<span color=''>abc</span>
        return=abc
    '''
    if s==None:return ""
    s=s.replace('</span>','')
    while True:
        startIndex,endIndex=findIndex(s,'<span','>')
        if startIndex!=-1:
            s=s[:startIndex]+s[endIndex+1:]
        else:break
    return s

def getTitle(s,TITLE_TAG='<h5>',TITLE_END_TAG='</h5>'):
    '''
    s中包含在TITLE_TAG，TITLE_END_TAG之间的内容是标题，返回标题。
    调用本方法要确保s包含TITLE_TAG，TITLE_END_TAG
    :param s: 
    :param TITLE_TAG: 起始标签
    :param TITLE_END_TAG:中止标签标签 
    :return: 
        1.TITLE_TAG，TITLE_END_TAG之间的标题，去掉了&nbsp;,\r,\n不可显示的字符
        2."",如果s中不存在TITLE_TAG，TITLE_END_TAG
        
        eg s=<h5><style>1.nbsp;1\n\r</style></h5>
           =>1.1
    '''
    def extractionTitle(s):
        s=removeTag(s)
        s=s.replace('&nbsp;','').replace('\r','').replace('\n','')
        return s
    startTag=TITLE_TAG
    endTag=TITLE_END_TAG
    s=findContent(s,startTag,endTag)
    return extractionTitle(s)


def trim_make_sure_have_tag(s,tag='<h5>'):
    '''
    把s中还有tag标签的地方都替换成tag,也就是这些标签不包含属性
    :param s: 
    :param tag:
    :return: 
    1.原样返回s
    2.所以的tag标签属性都被替代掉了
        eg s=<h5 color=1>test</h5>
        =><h5></h5>
    '''
    def ss(line):
        idx=line.find('>')
        return line[idx+1:] if idx>=0 else line
    if tag==None:return
    splits=s.split(tag[:-1])
    if len(splits)<=1:return
    sps1=map(ss,splits[1:])
    s=tag.join(sps1)
    return splits[0]+tag+s

def makeNode(name,tag):
    '''
    根据tag的类型生成节点
        
        tag:h1,h2,h3
            id
            name
            isQuestion=F
            children=[]
        tag:h4
            id
            name
            isQuestion=T
            children=[]
        tag:h5：
            id
            name
            其他的属性url,nd,cxd,zhd,answer,remark会在解析文档的时候补充
    :param name: 节点的名字，默认是root,否着是h1,h2,h3的标题
    :param tag: 标签的类型
    :return: 
    '''
    n={'id':str(uuid.uuid1()).replace('-',''),'name':name}
    if tag=="<h4>":
        n['isQuestion']=True
        n['children'] = []
    elif tag=="<h5>":
        pass
    else:#h1,h2,h3,default
        n['isQuestion']=False
        n['children'] = []
    return n
def getParagraphWithTag(s,tag):
    '''
    返回s中第一个以tag开头的段落
    :param s: 
    :param tag: 段落的标签
    :return: (node,FIRST_paragraph,remainS)
        node 表示一个节点的,由(id,name,isQuestion=F)组成，表示当前标签对应的node
        FIRST_paragraph：str,第一个包含tag的段落,包括【当前标签】和【当前标签的所有下级标签】
        remainS：str,等于(s-FIRST_paragraph)，剩余的【段落文档】

        返回有以下三种形式
        1.(None,None,None):s中不包含tag
        2.(node,some code,None):s是最后一个包含tag的code
        3.(node,some code,remainCode):默认情况
    '''
    sindex, eindex = findIndex(s, tag, tag)
    node, currentParam, remainS = None, None, None
    if sindex > -1:
        title = getTitle(s, tag, tag.replace("<","</"))
        if eindex>-1:
            currentParam=s[sindex:eindex]
            remainS=s[eindex:]
        else:
            currentParam=s[sindex:]
        node=makeNode(title,tag)
    return (node, currentParam, remainS)
def getNextTag(tag):
    dd={
        "<h1>": "<h2>",
        "<h2>": "<h3>",
        "<h3>": "<h4>",
        "<h4>": "<h5>"
    }
    return dd[tag]

def handleParagraphH5(paraGraph,node,extraParam):
    '''
    根据传入的h5段落内容
    1）解析paraGraph,并添加node节点的 nd,cxd,zhd,zsd,answer属性
    2) 把题目的内容(paraGraph去处nd,zxd,..answer的标注部分)
    保存到：
            extraParam.target_dir/extraParam.source_file-node.name.htm
            注意 node.name=知识点name-题号
    3)把node.name改称 还原成为原来 的tag.title(题号)

    4)这个程序唯一不严谨的地方是 假设【题目的答案】都在一行显示
    :param paraGraph:str,H5节点对应的段落文字
            eg:
            <h5>1</h5>
                知识度三角函数坡度

                难度0.15</p>

                综合度0.1</p>

                创新度0.1</p>

                答案C</p>

                已知甲、乙两坡的坡角分别为α、β，若甲坡比乙坡更陡些，则下列结论正确的是(    )</p>

            A. tanα<tanβ     B.sinα<sinβ     C. cosα<cosβ     D. cosα>cosβ  </p>

    :param node:dict, H5节点,也就是题目节点
    :param extraParam: 传入的额外参数,eg
        有如下参数
            target_base:$static_spring_path
            target_dir: $static_spring_path/2020-12-10
            source_file:勾股定理.html
            head标签：包括css样式
    :return:None
    '''
    def parseAttr(q):
        '''
        根据传入的段落字符串q,解析
        nd：float，出错=0
        cxd：float，出错=0
        zhd：float，出错=0
        zsd：不保留html样式
        answer:保留html样式，最长可以3000个字符
        
        :param q:str
        :return: nd,cxd,zhd,zsd,answer
        '''
        def ccc(q, tag):
            #提取q中tag与</p>之间的内容，返回不包括tag，但是包括了</p>
            s, t = findIndex(q, tag, '</p>')
            sss = q[s:t].replace("\n", ' ').replace(tag, '').replace("&nbsp;", "")
            return sss

        def ccc2(q, tag):
            #提取q中tag与</p>或者【答案结束】之间的内容，返回不包括tag，但是包括了</p>【答案结束】
            s, t = findIndex(q, tag, '</p>')
            s, t1 = findIndex(q, tag, '答案结束')
            t = t1 if t1 > 0 else t
            sss = q[s:t].replace("\n", ' ').replace(tag, '')
            return sss.strip()
        try:
            nd=float(removeTag(ccc(q,'难度')))
            cxd=float(removeTag(ccc(q,'创新度')))
            zhd=float(removeTag(ccc(q,'综合度')))
        except:
            nd,cxd,zhd=0,0,0

        zsd=removeSpanTag(ccc2(q,"知识度"))
        answer=removeSpanTag(ccc2(q,"答案"))


        if len(answer)>3000:
            answer=answer[0:3000]
        else:#选择题答案
            option_answer=removeTag(answer)
            if(option_answer in ['A','B','C','D']):
                answer=option_answer

        return (nd,cxd,zhd,zsd,answer)
    def saveFile(node,content):
        '''
        把 content保存到target_dir上，文件名由于
            htmlFileName和node.name 共同决定
            同时更新了node.url

        使用到extraParam下列参数：
            source_file:原文件名，生成目标文件名使用
            target_base：目标文件夹的根,计算url使用
            target_dir：目标文件夹
            head：html 样式
        :param node:一个h5节点
        :param content: 题目的内容
        :return: 
        '''
        #文件名+节点名 是保存的html名字

        #勾股定理.html
        sourceFileName=extraParam['source_file']
        #$static_spring_path
        target_base=extraParam['target_base']
        #$static_spring_path/2020-12-10
        target_dir = extraParam['target_dir']
        head=extraParam['head']

        #勾股定理
        src_name = sourceFileName.replace(".html", "").replace(".htm", "")
        #勾股定理的性质-17.html
        questionName=node['name']+'.htm'
        #勾股定理-勾股定理的性质-17.html
        savefileName=src_name+"-"+questionName
        #$static_spring_path/2020-12-10/勾股定理勾股定理的性质--17.html
        savePath=os.path.join(target_dir,savefileName)


        content = head + "<body lang=ZH-CN style='text-justify-trim:punctuation'>" + content+ '</body>'
        #/2020-12-10/勾股定理-17.html
        url =target_dir.replace(target_base,"")+"/"+savefileName
        node['url']=url
        with codecs.open(savePath, "w", "gbk") as fs:
            fs.write(content)

    nd, cxd, zhd, zsd, answer=parseAttr(paraGraph)
    node['nd']=nd
    node['cxd'] = cxd
    node['zhd'] = zhd
    node['zsd'] = zsd
    node['answer'] = answer

    #题目正文不显示答案
    _, newstart = findIndex(paraGraph, "答案", "</p>")
    question = paraGraph[newstart + len('</p>'):]
    saveFile(node,question)
    node['name']=node['name'].split('-')[-1]


def handleParagraphH4(paragraph,node,extraParam):
    '''
    解析paragraph,提取出攻略来
    1)把攻略的内容保存到
        extraParam.target_dir/extraParam.source_file-node.name.html
    2)更新node.remark指向上述的url

    :param paraGraph:H4节点对应的段落文字
    :param node: H4节点,也就是题目节点
    :param extraParam: 传入的额外参数,eg
        有如下参数
            target_base:$static_spring_path，生成目标文件名使用
            target_dir: $static_spring_path/2020-12-10，生成攻略url使用(node.remark)
            source_file:勾股定理.html，生成目标文件名使用
            head标签：包括css样式
    '''

    def saveFile(node,content):
        '''
        把 content保存到target_dir上，文件名由于
            htmlFileName和node.name 共同决定
        添加node.remark属性=攻略.url

        使用到extraParam下列参数：
            source_file:原文件名
            target_base：目标文件夹的根
            target_dir：目标文件夹
            head：html 样式
        :param node:一个h5节点
        :param content: 题目的内容
        :return:
        '''
        #文件名+节点名 是保存的html名字

        #勾股定理.html
        sourceFileName=extraParam['source_file']
        #$static_spring_path
        target_base=extraParam['target_base']
        #$static_spring_path/2020-12-10
        target_dir = extraParam['target_dir']
        head=extraParam['head']

        #勾股定理
        src_name = sourceFileName.replace(".html", "").replace(".htm", "")
        #勾股定理的证明.html
        questionName=node['name']+'.htm'
        #勾股定理-勾股定理的证明.html
        savefileName=src_name+"-"+questionName
        #$static_spring_path/2020-12-10/勾股定理-勾股定理的证明.html
        savePath=os.path.join(target_dir,savefileName)


        content = head + "<body lang=ZH-CN style='text-justify-trim:punctuation'>" + content+ '</body>'
        #/2020-12-10/勾股定理-17.html
        url =target_dir.replace(target_base,"")+"/"+savefileName
        node['remark']=url
        with codecs.open(savePath, "w", "gbk") as fs:
            fs.write(content)

    tag1='攻略'

    ss,tt = findIndex(paragraph,tag1, "<h5")
    if(ss>=0):
        remark=removeSpanTag(paragraph[ss:tt])
        saveFile(node,remark)


def handleParagraph(paragraph,tag,parent,extraParam):
    '''
    解析【段落】文档,找到，paragraph中的所有tag标签，把他转换成为一个一个node,添加到
    parent.children中。注意：
    1）遇到每个标签，都把他转成一个node=(id,name,isQuesteoin,children...[]),并且维护他的子结构
    2) 本方法没有返回值，更新全部反映到parent.children中
    3)除了tag=H5的标签以外，其他标签所对应node.name=tag.innerText()
      而tag=H5的时候，node.name=parent.name-tag.innerText(),(知识点名称-题号)
      为的是保证节点名称的唯一性（不同知识点的题号可以相同）
    tag表示生成那个级别的 tree
    <h1>,<h2>....
    
    A。每次遇到一个tag标签，就把他转成一个node,添加到parant.children下面。
    B。处理tag下一级的标签内容
    
    备注：文档结果是嵌入式的,处理采用深度优先的算法，先H1->H2..->H5 ->H1....
    所以本方法的递归，是【深度优先】的策略
    <h1></h1>
        <h2></h2>
            <h3></h3>
                <h4></h4>
                    <h5></h5>
    ....
    <h1></h1>
        <h2></h2>
            <h3></h3>
                <h4></h4>
                    <h5></h5>
    :param paragraph: 当前段落的内容,string
    :param tag: 当前要处理的标签,eg h1,h2...,
    :param parent: node节点,本节所【生成的节点】的【父节点】
            例如tag=h1, parent=root
                tag=h2, parent=node(h1)
    :param extraParam: 传入的额外参数,eg
        有如下参数
            target_base:$static_spring_path
            target_dir: $static_spring_path/2020-12-10
            source_file:勾股定理.html
            head标签：包括css样式
    :return: 
    '''
    s=trim_make_sure_have_tag(paragraph,tag)
    while s is not None:
        #当前的tag转成node,paragraph与node对应,s表示下一次循环使用的段落文档
        node, paragraph, s = getParagraphWithTag(s,tag)

        if (node is None): break

        #父节点添加子节点
        parent['children'].append(node)

        #h5比较特殊，表示这是一个题目，h5
        if(tag=='<h5>'):
            node['name']=parent['name']+'-'+node['name']
            handleParagraphH5(paragraph,node,extraParam)
        elif(tag=='<h4>'):#h4是知识点，里面有攻略，也要”特殊处理“
            handleParagraphH4(paragraph,node,extraParam)
            handleParagraph(paragraph,getNextTag(tag),node,extraParam)
        else:
            #处理下一级别的标签
            handleParagraph(paragraph,getNextTag(tag),node,extraParam)

def handleHtml(htmlFileName,extraParam):
    '''
    把输入html文件转化成为一棵tree,并且返回
    
    把html文件分割成（head,body,body）=>tree,
    head是样式文件的内容。把head加入到extraParam中。

    可以这么理解：
    htmlFileName==>extraParam.target_dir/extraParam.source_file 的”文件转换“
    :param htmlFileName: 输入的html的全路径，
            eg.../upload/2020-12-10/勾股定理.html

    :param extraParam: 传入的额外参数,eg
        有如下参数
            target_base:$static_spring_path
            target_dir: $static_spring_path/2020-12-10
            source_file:勾股定理.html

            .../$static_spring
    :return: {"success":True|False,
              "tree":root :optional 
              "message":optional
              }
    '''
    html=readDoc(htmlFileName)
    if html == "": return {"success": False, "message": "文档%s是空"%htmlFileName}

    head=findHtmlHead(html)
    if head=="":return {"success":False,"message":"文档没有head"}

    body=findHtmlBody(html)
    if body == "": return {"success": False, "message": "文档没有body"}


    extraParam['head']=head
    root=makeNode("root",tag=None)

    handleParagraph(body,"<h1>",root,extraParam)
    return {"success":True,"tree":root}


def hanleFiles(srcpath, target,extraParam):
    '''
    把srcpath下面的[文件]或[文件夹]，经过处理，搬运到target下面。
    本方法会递归调用自己！但是递归只有2层
    1层：srcpath是上传路径,下面的文件是本次上传题目的[日期目录],eg：2020-12-10
    2层：srcpath是日期目录，下面的文件是 资源目录(*.files) 或者 题目(*.html)

    遍历srcpath下面的文件f：
        1.f 是html文件,
            A.设置extraParam的source_file,target_dir属性，用于把source_file复制到target_dir上使用
            B.调用handleHtml(srcpath,extraParam=extraParam)，把html转换为一个tree,保存到target_dir
            
        2.f 是 .files文件夹，把f移动到target上面，这里先删除了target.f,返回在复制srcpath.f
        3.f 既不是1 也不是2,而是一个文件夹，例如2020-12-10,在target上面创建f,处理srcpath.f下级的文件
        
    :param srcpath: 一定是一个目录路径
    :param target: 一定是一个目录路径,与srcpath平级的
    :param extraParam: 
    :return:
        第二层递归的返回
        list(state),list.size=srcpath下面html的数量(题库目录下的文件数量)
        state={
                  "success":True|False,
                 "tree":[tree1,tree2...] :optional
                  "message":optional  //success False 会有这个字段，表示不成功的原因
                }

        第一层递归的返回list(state),把第二层递归的返回的所有list
        合成一个大的list,list.size=srcpath下面的所有html文件的数量

    '''

    def isHtml(f):
        return f.endswith('.htm') or f.endswith('.html')
    def isRecources(f):
        return f.endswith('.files')
    def mkdir(fname):
        #在target上创建fname,文件夹不存在的时候创建
        t=os.path.join(target,fname)
        if os.path.exists(t)==False:
            os.mkdir(t)
    def updateResourceFile(resfile):
        #删除[目标]下的[资源目录.files]，然后复制[原目录]的[资源目录.files]到目标
        ss=os.path.join(srcpath, resfile)
        tt=os.path.join(target, resfile)
        if (os.path.exists(tt)):
            shutil.rmtree(tt)
        shutil.copytree(ss, tt)

        #为了pdf准备的目录
        gtt=os.path.join(extraParam['generate_path'], resfile)
        if (os.path.exists(gtt)):
            shutil.rmtree(gtt)
        shutil.copytree(ss, gtt)

    result=[]
    files = os.listdir(srcpath)#files只是文件名
    for f in files:
        #目录下面的所有图片移动到目标去
        if isRecources(f):#2
            updateResourceFile(f)
        elif isHtml(f):#1
            extraParam['target_dir']=target
            extraParam['source_file']=f
            html_result=handleHtml(os.path.join(srcpath, f),extraParam=extraParam)
            result.append(html_result)
        else:#3,递归
            mkdir(f)
            lower_result=hanleFiles(os.path.join(srcpath, f), target=os.path.join(target, f),extraParam=extraParam)
            result.extend(lower_result)
    return result
def removeDir(baseroot):
    '''
    删除baseroot下的所有文件和文件夹
    :param baseroot: 
    :return: 
    '''
    files=os.listdir(baseroot)
    for f in files:
        filename=os.path.join(baseroot,f)
        shutil.rmtree(filename)

def readJsonFile(filename,default=[]):
    '''
    读取json文件
    :return 
        1.[],出错或者文件不存在
        2.json object
    '''
    if os.path.exists(filename) == False:
        return default
    try:
        with codecs.open(filename, "r", "utf-8") as fs:
            return json.load(fs)
    except :
        return default


#===================树结构数据的相关函数==================================
def _node_eq(a,b):
    '''
    
    :param a:node 节点
    :param b:node 节点 
    :return: 
    '''
    return a['name']==b['name']
def _node_assign(a,b):
    '''
    a<=b,题目之间的赋值
    :param a:题目的node 节点
    :param b:题目的node 节点 
    :return: 
    '''
    field=['name','nd','cxd','zhd','zsd','answer','url']
    for f in field:
        a[f]=b[f]
def _node_assign_notH5(a,b):
    '''

    :param a:h1,h2,h3,h4
    :param b:h1,h2,h3,h4
    :return:
    '''
    field=['remark']
    for f in field:
        if f in b:
            a[f]=b[f]

def _node_isQuestion(a):
    return ('children' in a)==False
def _node_isZsd(a):
    return a['isQuestion']
def _node_set_merge(A,b):
    '''
    把节点b合并到集合A中，执行如下操作：
    A.如果存在a in A, a==b,那么合并a,b.
    B.否则b添加到集合A中。
    
    :param A: list of node,每个元素都是与b同级的.
            eg:
                b=h3
                A就有多个h3组成
    :param b: node 节点
    :return: 
    '''
    assert isinstance(A,list) , "节点集合A必须是list类型"
    assert isinstance(b, dict), "节点b必须是dict类型"

    addB2A=True
    for a in A:
        if _node_eq(a,b):
            addB2A=False
            _node_merge(a,b)
            break
    if addB2A:A.append(b)

def _node_merge(a,b):
    '''
    合并两个相等的节点
    1.如果a,b是H5节点，进行a<=b.
    2.否则 把b的children 合并到a的children下面。
    :param a: node 节点
    :param b: node 节点
    :return: 
    '''
    assert isinstance(a,dict) and isinstance(b,dict),"节点必须是dict类型"
    assert _node_eq(a,b),"节点必须相等才可以调用本方法"

    if _node_isQuestion(a):
        _node_assign(a,b) # a<=b
    else:

        _node_assign_notH5(a,b)
        a_children = a.get('children')
        b_children=b.get('children')
        for bc in b_children:
            _node_set_merge(a_children,bc)
#========================================================================


def tree2Sqls(trees, parentId):
    '''
    把树的每个节点存成一个record,并且维护好树的上下级关系
    :param trees:list of tree(node)|question
    :param parentId: 父ID
    :return: list of sqls
    '''
    def node2Record(node):
        '''
        :param node: 一个tree上的node节点
        :return: 节点对应的record,sql语句
        '''
        assert isinstance(node,dict),'node 必须是dict'
        isLeaf=1 if node['isQuestion']  else 0
        remark=node['remark'] if 'remark' in node else ''
        return "INSERT INTO chapter(uid,NAME,parent,isLeaf,remark) VALUES('%s','%s','%s',%d,'%s');"%(node['id'], node['name'], parentId, isLeaf,remark)

    def questionNode2Record(questionNode):
        '''
        
        :param questionNode: 题目节点，有许多特殊属性（url,nd,cxd,zsd,zhd,answer）
        :param sqls: 
        :return: 所有question节点对应的records[],每个元素是一个 sql insert语句。
            
        '''
        assert isinstance(questionNode, dict), 'questionNode 必须是dict'
        d=questionNode
        sql_str = "INSERT INTO question(uid,title,url,catalog,difficult,complex,creative,remark,answer) VALUES ('%s'," \
                      "'%s','%s','%s',%f,%f,%f,'%s','%s');" % (
                      d['id'], d['name'].replace("'", ''), d['url'].replace("'", ''), parentId, d['nd'], d['zhd'],
                      d['cxd'], d['zsd'].replace("'", ''), d['answer'].replace("'", ''))
        return sql_str

    assert isinstance(trees,list),'trees 必须是list'
    sqls=[]
    for tree in trees:
        tree['parent']=parentId
        #有没有children属性是区分题目与非题目的标志
        if "children" in tree:
            sqls.append(node2Record(tree))
            children_sqls=tree2Sqls(tree['children'], tree['id'])
            sqls.extend(children_sqls)
        else:
            sqls.append(questionNode2Record(tree))
    return sqls


def overWriteOldVersion(jsonObj, path):
    '''
    更新json库
    '''
    with codecs.open(path, "w", "utf-8") as fs:
        sss=json.dumps(jsonObj, ensure_ascii=False,indent=2)
        fs.write(sss.encode('utf-8').decode('utf-8'))
#========================================================================
def service(config):
    '''
    1.把config.src_path下面的每个文档(html)转换成为一棵树tree,所有
        文档的tree组成集合trees.
        node=[id,name,children[node],isQuestion,url,nd,zsd,cxd,zsd,answer]
        
        tree=node(id,"root",children[node(h1)],F)
        
        根据文档标签的不同，对应的node结果也不同
        A."root",h1,h2,h3,h4的node结构:[id,name,children[node],isQuestion]
            A.1：h1,h2,h3,root的isQuestion=False
            A.2:h4的isQuestion=True
        B.h5的node结构[id,name,url,nd,zsd,cxd,zsd,answer],表示一个题目
        
    2.把上述所有的trees进行合并,合并原则是有相同的节点名称,得到new_merged_trees=list。
    3.把config.src_path下面的每个文档(html)切割成一个个题目,
        题目名=文档名+知识点标题(h4)+题目标题(h5)+".html",保存到config.dst_path
        对应目录下.
    4.读取config.json_output保存的数据库版本的 题库结构，与（2）的new_merged_trees合并，
    然后:
        A.全量更新mysql数据库（删除chapter,question表）
        B.用合并的新trees覆盖config.json_output
        C.删除config.src_path上传的文件
        
    :param config: 需要 src_path,dst_path,json_output,generate_path
                    以及数据库连接相关信息。
                  generate_path
                  json_output:目录结构文件st.json
                  dst_path:springboot 的静态目录，用于题目的显示
                  src_path:下目录结构
                    eg:
                       2020-10-01
                            勾股定理.html
                            勾股定理.files
                            ....
                       2020-10-11
                            一次函数.html
                            一次函数.files
                            ....
                    ....
    :return: {"success":True,"err":[]}
    err：解析某个html如果出错，会把错误消息加入这个数组。
    '''

    #src_path:/home/mathai/projects/db/upload
    #dst_path:spring.resources.static-locations,spring的静态目录
    src_path, dst_path = config['src_path'], config['dst_path']
    generate_path=config['generate_path']

    extraParam={"target_base":dst_path,"generate_path":generate_path}
    #html_trees=list(element),每个元素对应一个html生成的tree

    html_trees=hanleFiles(src_path,dst_path,extraParam)


    #html_trees的每个文档要进行合并
    new_merged_trees=[]
    errors=[]
    for r in html_trees:
        if r['success']:
          _node_set_merge(new_merged_trees,r['tree'])
        else:
            errors.append(r['message'])

    #更新题库
    oldTrees=readJsonFile(config['json_output'])
    for r in new_merged_trees:
        _node_set_merge(oldTrees,r)


    #从这以后才落地

    #node(json)->record(mysql)
    sqls=tree2Sqls(oldTrees,"")
    insert_file_rec(config['ip'], config['dbname'], config['username'], config['password'], sqls)

    overWriteOldVersion(oldTrees,config['json_output'])

    removeDir(config['src_path'])

    return {"success":True,"err":errors}
if __name__ == '__main__':
    # s='/home/mathai/桌面/update/src'
    # t='/home/mathai/桌面/update/dst'
    # json_output='/home/mathai/projects/db/static/chapterdb/st1.json'
    # config={
    #     'src_path':s,
    #     'dst_path':t,
    #     'json_output':json_output
    # }
    # config=defaultConfig()
    # service(config=config)


    s='</span><span lang=EN-US style=font-size:10.5pt;font-family:"Calibri",sans-serif;posi' \
      'tion: relative;top:10.5pt><img width=27 height=42 src="勾股、实数.files/image268.png"></span><span ' \
      'style=font-size:12.0pt;font-family:等线;color:black>的双重非负性</span>'
    print(s)
    s=removeSpanTag(s)
    print(s)