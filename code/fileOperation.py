import boto3
from botocore.exceptions import NoCredentialsError
import sqlite3
import yaml
from datetime import datetime
import os
from pathlib import Path
import db_connection, db_instance

#yml_file_path = '..\\secret.yaml'
# yml_file_path = 'C:\\0.git\\tech-titans-AI\\secret.yaml'
yml_file_path = 'tech_titan\\tech-titans-AI\\secret.yaml'


def s3_connection():
    try:
        # s3 클라이언트 생성
        with open(yml_file_path) as f:
            yaml_info = yaml.load(f, Loader=yaml.FullLoader)
            s3_info = yaml_info['s3_info']

            s3 = boto3.client(
                service_name="s3",
                region_name="ap-northeast-2",
                aws_access_key_id = s3_info['AWS_ACCESS_KEY_ID'],
                aws_secret_access_key = s3_info['AWS_SECRET_ACCESS_KEY'],
            )
    except Exception as e:
        print(e)
    else:
        print("s3 bucket connected!") 
        return s3
        
s3 = s3_connection()

def make_raw_file_name(isRowFile):
    upload_date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    upload_date = upload_date_time.split(" ")[0]
    upload_date = upload_date.replace("-", "")
    upload_time = upload_date_time.split(" ")[1]
    upload_time = upload_time.replace(":", "")
    if (isRowFile):
        raw_file_name = "R_L01_" + upload_date + "_" + upload_time + ".png"
    else:
        raw_file_name = "A_L01_" + upload_date + "_" + upload_time + ".png"
    return raw_file_name, upload_date_time


def upload_to_s3(file_name, upload_date_time):
    try:
        s3.upload_file(file_name, 'tech-titans-s3', file_name)
        print(f"{file_name} has been uploaded to tech-titans-s3")
        return file_name, upload_date_time
    except FileNotFoundError:
        print("The file was not found")
    except NoCredentialsError:
        print("Credentials not available")

def save_file_info_to_raw_file_table(file_path, upload_date_time):

    # 파일 경로
    #file_path = "red5.jpg"

    # 파일 객체 생성
    file = Path(file_path)

    # 파일 이름
    file_name = file.name
    print(f"파일 이름: {file_name}")

    # 파일 확장자 추출
    file_extension = file.suffix
    print(f"파일 확장자: {file_extension}")

    # 파일 크기 추출
    file_size = os.path.getsize(file_path)
    print(f"파일 크기: {file_size} 바이트")
    

    new_row_file = db_instance.RawFile(
    saved_file_name = file_name,
    created_at = upload_date_time,
    updated_at = upload_date_time,
    content_type = file_extension,
    file_size = file_size,
    saved_path =f"https://tech-titans-s3.s3.amazonaws.com/{file_name}"
    )
    db_connection.insert_raw_file_data(new_row_file, db_connection.connect_mysql())

def save_file_info_to_analyzed_file_table(file_path, upload_date_time, is_passed, raw_file_name, defect_severity):

    # 파일 경로
    #file_path = "red5.jpg"

    # 파일 객체 생성
    file = Path(file_path)

    # 파일 이름
    file_name = file.name
    print(f"파일 이름: {file_name}")

    # 파일 확장자 추출
    file_extension = file.suffix
    print(f"파일 확장자: {file_extension}")

    # 파일 크기 추출
    file_size = os.path.getsize(file_path)
    print(f"파일 크기: {file_size} 바이트")
    

    new_analyzed_file = db_instance.AnalyzedFile(
    saved_file_name = file_name,
    created_at = upload_date_time,
    updated_at = upload_date_time,
    content_type = file_extension,
    file_size = file_size,
    is_passed = is_passed,
    raw_file_name = raw_file_name,
    saved_path =f"https://tech-titans-s3.s3.amazonaws.com/{file_name}",
    defect_severity = defect_severity
    )
    db_connection.insert_analyzed_field_data(new_analyzed_file, db_connection.connect_mysql())


