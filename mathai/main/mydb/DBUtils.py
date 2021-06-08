__author__ = 'zlsyt'
import pymysql

from mathai.main.config.MyConfig import defaultConfig


#https://juejin.im/entry/5ac32368f265da23750715b2
def connect_wxremit_db(ip,dbname,username,password):
    return pymysql.connect(host=ip,
                           port=3306,
                           user=username,
                           password=password,
                           database=dbname,
                           charset='utf8')
class DBManager:
    def __init__(self,config):
        self.config=config
        self.conn=connect_wxremit_db(ip=config['ip'],username=config['username'],dbname=config["dbname"],password=config['password'])
        print("success create db connection")

    #查询，返回list of tuple
    def select(self,sql):
        cur = self.conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        return rows
    def insert(self,sqls):
        try:
            cur = self.conn.cursor()
            for i,sql_str in enumerate(sqls):
                cur.execute(sql_str)
                if i%100==0:
                    self.conn.commit()
        except:
            self.conn.rollback()
            raise
        finally:
            self.conn.commit()
            cur.close()
if __name__ == '__main__':
    db=DBManager(defaultConfig())
    db.select("SELECT uid,title,url,catalog,difficult,complex,creative,remark,answer  from Question where catalog in (select DISTINCT zsdid from StudentPlan where studentid='1897290');")