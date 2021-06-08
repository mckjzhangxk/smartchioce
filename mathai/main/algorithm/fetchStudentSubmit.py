__author__ = 'mathai'
import click

from mathai.main.mydb.DBUtils import DBManager
from mathai.main.config.MyConfig import defaultConfig


fetch_sql='''


SELECT
       t.hwid,
	   t.studentid,
       teacher.teacher_id,
	   (case when t.result='U'
       then 'F'
       else
       t.result END) as result,
       t.questionid,
       q.catalog,
       q.difficult,
       q.complex,
       q.creative,
       q.url
       FROM studentsubmit t,question q,studentteacher teacher
where t.questionid=q.uid
and teacher.student_id=t.studentid
and t.handle='T'
and t.studentid!='1897290'
order by t.studentid,hwid;



'''

fields='日期  学生ID    老师ID    是否正确    问题ID    问题专题ID  难度  复杂度 创新度 url'

def dump2file(filename,rows):
    with open(filename,'w') as fs:
        fs.write(fields)
        fs.write('\n')
        for line in rows:
            fs.write('\t'.join(map(str,line)))
            fs.write('\n')

@click.command()
@click.option('--output_path','-o','output_path',required=True,type=click.Path(False),help='the export path')
def exportData(output_path):
    config=defaultConfig()
    dbm=DBManager(config)
    rows=dbm.select(fetch_sql)
    dump2file(output_path,rows)
if __name__ == '__main__':
    exportData()