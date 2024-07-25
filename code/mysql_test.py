import pymysql
import yaml

with open('secret.yaml') as f:
    try:
        db = yaml.load(f, Loader=yaml.FullLoader)
    except:
        print('yaml 파일 로드 실패')

db_info = db['mysql_info']

conn = pymysql.connect(
    host = db_info['url'],
    port = 3306, 
    user = db_info['username'], 
    passwd = db_info['password'],
    database = db_info['database_name']
)

if conn:
    print(conn)
    print('DB 연결 설공')
else:
    print('DB 연결 실패')

cur = conn.cursor()

try:
    cur.execute("select * from uploaded_file")
    result = cur.fetchall()
    print(result)
except:
    print('쿼리문 작성 오류')


# insert 쿼리문 2개

# def insert_inspection_data():

# def insert_photo_data():

# select 쿼리문 4개

# def select_all_count()
# def select_all_inspection()
# def select_all_inspection_count()
# def select_defect_count()