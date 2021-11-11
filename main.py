import os, time, sys
import configparser
import psycopg2
import logging

logging.basicConfig(level=logging.DEBUG,
                    filename='logging.log',
                    datefmt='%Y/%m/%d %H:%M:%S',
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if len(sys.argv) < 2 or len(sys.argv) > 4:
    logger.error("没有输入参数")
    print("请输入参数")
    exit(0)
elif len(sys.argv) > 3:
    logger.error("参数输入错误")
    print("参数个数错误")
    exit(0)
else:
    sqlName = sys.argv[1]
    sqlCommand = sys.argv[2]

def replace_data(sqlName):
    with open("{}.sql".format(sqlName), "rt") as file:
        x = file.read()

    with open("{}.sql".format(sqlName), "wt") as file:
        x = x.replace("hlink-saas-manage", sqlName)
        file.write(x)


def run_bash(cmd):
    with open("run1.sh", "w")as f:
        f.write(cmd)
    os.system("bash run1.sh >/dev/null 2>&1")
    run_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    if "-q -W -f" in cmd:
        logger.info("数据库写入成功")
        print(run_time, "数据库写入成功")
    if "-n" in cmd:
        logger.info("数据库备份成功")
        print(run_time, "数据库备份成功")
    if "SELECT" in cmd:
        logger.info("数据库队列刷新成功")
        print(run_time, "数据库队列刷新成功")


def tables_list(database, user, password, host, port):
    try:
        conn = psycopg2.connect(database=database, user=user, password=password, host=host,
                                port=port)
    except:
        print("连接失败，请检查配置文件")
        exit(1)
    cur = conn.cursor()
    # 执行查询命令
    cur.execute("select * from pg_tables")
    #    print("正确链接数据库")

    rows = cur.fetchall()
    tablesList = []
    for i in rows:
        if i[0] not in tablesList:
            tablesList.append(i[0])

    return tablesList

def insert_sql(database, user, password, host, port):
    sqlStatement = """INSERT INTO {}.user ( account_id, name, active_flag, delete_flag, is_tenant_admin, update_by, update_time, create_by, create_time)
VALUES ({}, 'admin', 1, 0, 1, 1, 1, 1, 1);""".format(sqlName, sqlCommand)
    try:
        conn = psycopg2.connect(database=database, user=user, password=password, host=host,
                                port=port)
        cur = conn.cursor()
        # 执行查询命令
        cur.execute(sqlStatement)
        conn.commit()
        conn.close()
        logger.info("")
    except Exception as e:
        print("连接失败 {}".format(e))

def main(database, user, password, host, port, schema):
    if sys.argv[1] in tables_list(database, user, password, host, port):
        logger.critical("数据中的{}表已存在".format(sys.argv[1]))
        print("{}已经存在，请检查后运行".format(sys.argv[1]))
        exit(1)
        # database，user，password，host，port分别对应要连接的PostgreSQL数据库的数据库名、数据库用户名、用户密码、主机、端口信息，请根据具体情况自行修改
    copyOutCmd = """#!/bin/bash
expect <(cat <<'END'
set password "{}"
spawn pg_dump -h {} -p {} -U {} -W -d {} -n {} -f {}.sql
expect "Password:"
send "$password\r"
interact
END
)""".format(password, host, port, user, database, schema, sqlName)

    copyInCmd = """#!/bin/bash
expect <(cat <<'END'
set password "{}"
spawn psql -h {} -p {} -U {} -d {} -q -W -f {}.sql
expect "Password:"
send "$password\r"
interact
END)""".format(password, host, port, user, database, sqlName)

    refreshseqCmd = """#!/bin/bash
expect <(cat <<'END'
set password "{}"
spawn psql -h {} -p {} -U {} -d {} -q -W -c "SELECT \"public\".\"set_sequence\"({})"
expect "Password:"
send "$password\r"
interact
END
)""".format(password, host, port, user, database, sqlName)
    try:
        start_time = time.time()
        run_bash(copyOutCmd)
        replace_data(sqlName)
        run_bash(copyInCmd)
        run_bash(refreshseqCmd)
        os.system("rm run1.sh {}.sql".format(sqlName))
        insert_sql(database, user, passwd, host, port)
        logger.info("{}插入数据库完成".format(sqlCommand))
        print("共计用时{:.2f}秒".format(time.time() - start_time))
    except PermissionError:
        logger.warning("没有在root用户下运行")
        print("请在root用户下运行")


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read("./config.ini")
    try:
        host = config['postgresql']['host']
        user = config['postgresql']['user']
        passwd = config['postgresql']['password']
        db = config['postgresql']['database']
        schema = config['postgresql']['schema']
        port = config['postgresql']['port']

        main(db, user, passwd, host, port, schema)
    except KeyError:
        logger.warning("没有在/app/createSql目录下运行")
        print("请在/app/createSql目录下运行main.py")
