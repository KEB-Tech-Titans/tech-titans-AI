import pymysql
import yaml

from pymysql import Error
from db_instance import *
from datetime import datetime

# db_info_file_path = 'C:\\0.git\\tech-titans-AI\\secret.yaml'
db_info_file_path = 'tech_titan\\tech-titans-AI\\secret.yaml'

def connect_mysql():
    with open(db_info_file_path) as f:
        try:
            db = yaml.load(f, Loader=yaml.FullLoader)
        except:
            print('yaml 파일 로드 실패')

    db_info = db['mysql_info']
    
    try:
        conn = pymysql.connect(
            host = db_info['url'],
            port = 3306, 
            user = db_info['username'], 
            passwd = db_info['password'],
            database = db_info['database_name']
        )
    except Error as e:
        print(f'DB connection Error : {e}')

    return conn

# insert 쿼리문 3개

# 각각 db의 인스턴스 만들고 쿼리 수행

def insert_analyzed_field_data(analyze_file, conn):
    try:
        with conn.cursor() as cursor:
            query='''
                INSERT INTO analyzed_file (saved_file_name, created_at, updated_at, content_type,
                file_size, is_passed, raw_file_name, saved_path)
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
            '''

            cursor.execute(query,(
                analyze_file.saved_file_name,
                analyze_file.created_at,
                analyze_file.updated_at,
                analyze_file.content_type,
                analyze_file.file_size,
                analyze_file.is_passed,
                analyze_file.raw_file_name,
                analyze_file.saved_path
            ))
            conn.commit()
        
    except Error as e:
        print(f'Error:{e}')

def insert_raw_file_data(raw_file, conn):
    try:
        with conn.cursor() as cursor:
            # 파라미터화된 쿼리
            query = '''
                INSERT INTO raw_file (saved_file_name, created_at, updated_at, content_type, file_size, saved_path)
                VALUES (%s, %s, %s, %s, %s, %s)
            '''
            
            # 데이터 삽입
            cursor.execute(query, (
                raw_file.saved_file_name,
                raw_file.created_at,
                raw_file.updated_at,
                raw_file.content_type,
                raw_file.file_size,
                raw_file.saved_path
            ))
            conn.commit()
            
            print("Data inserted successfully")
    
    except Error as e:
        print(f"Error: {e}")

def insert_inspection_data(inspection, conn):
    try:
        with conn.cursor() as cursor:
            query = '''
                insert into inspection (created_at, updated_at, analyzed_file_name, area, defect_type)
                values (%s,%s,%s,%s,%s)
            '''

            cursor.execute(query, (
                inspection.created_at,
                inspection.updated_at,
                inspection.analyzed_file_name,
                inspection.area,
                inspection.defect_type
            ))
            conn.commit()
    except Error as e:
        print(f'Error:{e}')

# select 쿼리문 4개

def select_all_count(conn):
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    
    with conn.cursor() as cursor:
        try:
            query = "SELECT COUNT(created_at) FROM raw_file WHERE created_at LIKE %s"
            cursor.execute(query, (today + '%'))
            result = cursor.fetchone()
            return result[0]  # 튜플의 첫 번째 요소를 반환
        except Error as e:
            print(f"DB Select Query Error: {e}")
            return 0

def select_all_inspection_count(conn):
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    with conn.cursor() as cursor:
        try:
            query = "SELECT COUNT(*) FROM analyzed_file WHERE created_at LIKE %s and is_passed = false"
            cursor.execute(query, (today + '%'))
            result = cursor.fetchone()
            return result[0]  # 튜플의 첫 번째 요소를 반환
        except Error as e:
            print(f'DB selection Error: {e}')
            return 0

def select_defect_count(conn):
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    with conn.cursor() as cursor:
        try:
            query = '''
                SELECT defect_type, COUNT(*) as count
                FROM inspection
                WHERE created_at like %s
                GROUP BY defect_type;
            '''
            
            cursor.execute(query, (today + '%'))
            results = cursor.fetchall()
            # 결과를 사전 형태로 변환
            defect_ratio = {row[0]: row[1] for row in results}
            return defect_ratio
        except Error as e:
            print(f'DB selection Error : {e}')
            return {}


# test