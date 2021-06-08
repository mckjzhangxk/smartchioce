import pymysql
#https://juejin.im/entry/5ac32368f265da23750715b2
def connect_wxremit_db(ip,dbname,username,password):
    return pymysql.connect(host=ip,
                           port=3306,
                           user=username,
                           password=password,
                           database=dbname,
                           charset='utf8')


def insert_file_rec(ip,dbname,username,password,sqls):
        conn=connect_wxremit_db(ip,dbname,username,password)
        cur = conn.cursor()
        try:
            cur.execute('delete from chapter');
            cur.execute('delete from question');
            conn.commit();
            for i,sql_str in enumerate(sqls):
                cur.execute(sql_str)
                if i%100==0:
                    conn.commit()
            conn.commit();
        except:
            conn.rollback()
            print(sql_str)
            raise
        finally:
            cur.close()
            conn.close()

def array2Sql(rr,sqls,parent):
    def dto2Sql(d):
        sql_str = "INSERT INTO question(uid,title,url,catalog,difficult,complex,creative,remark,answer) VALUES ('%s'," \
                          "'%s','%s','%s',%f,%f,%f,'%s','%s');"%(d['id'],d['title'].replace("'",''),d['url'].replace("'",''),parent,d['nd'],d['zhd'],d['cxd'],d['zsd'].replace("'",''),d['answer'].replace("'",''))
        return sql_str
    for d in rr:
        sqls.append(dto2Sql(d))
def json2Sql(rr,sqls,parent):
    # 知识点是叶子节点
    def dto2Sql(dto):
        isLeaf=0 if "children" in dto else 1
        return "INSERT INTO chapter(uid,NAME,parent,isLeaf) VALUES('%s','%s','%s',%d);"%(dto['id'],dto['name'],parent,isLeaf)
    for d in rr:
        sqls.append(dto2Sql(d))
    for d in rr:
        if "children" in d:
            json2Sql(d['children'],sqls,d['id'])
        if "questions" in d:
            array2Sql(d['questions'],sqls,d['id'])

def data2DB(config,data):
    sqls=[]
    json2Sql(data,sqls,"")
    insert_file_rec(config['ip'],config['dbname'],config['username'],config['password'],sqls)


