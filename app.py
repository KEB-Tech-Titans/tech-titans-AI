import subprocess
import sys

# 패키지를 설치하는 함수
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# 필요한 패키지 목록
required_packages = [
    "flask",
    "werkzeug",
    "opencv-python",
    "numpy",
    "matplotlib",
    "ultralytics"
]

# 패키지 설치
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        install(package)

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
import cv2
import json 
from socket import *
from http import HTTPStatus

import segment_model
from io import BytesIO
import numpy as np
import matplotlib.pyplot as plt

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 스마트폰 표면 분석
@app.route('/analyze', methods=['POST'])
def analyze():
    print('받음')

    file = request.files['imageFile']

    print(file.content_length)

    if file.filename == '':
            return jsonify({"error": "There is no file"}), 400
    
    print("spring boot한테 받은 파일 이름" + file.filename)

    response = jsonify({"data": file.filename + ' -from Flask-', "status": HTTPStatus.OK})
    print(response)

    # 파일을 저장해서 확인용
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.seek(0)  # 파일 포인터를 처음으로 되돌림
    file.save(filepath)
    print(f"파일이 저장된 경로: {filepath}")

    # 저장된 파일의 존재 여부와 크기 확인
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found after saving"}), 400

    if os.path.getsize(filepath) == 0:
        return jsonify({"error": "Saved file is empty"}), 400


    # 미리 만들어진 모델에 이미지 넣어서 분석
    img, results = segment_model.predict_image_segment(filepath)

    dto_result = {}

    # 나중에 분석 이미지 파일 같이 보내기
    # dto_result['image'] = convert_to_serializable(img)
    dto_result['inspections'] = []

    for result in results:
        temp_dict = {}

        # numpy 타입 일반 타입으로 변환
        temp_dict['class'] = convert_to_serializable(result['class'])
        temp_dict['conf'] = convert_to_serializable(result['conf'])
        temp_dict['area'] = convert_to_serializable(result['area'])

        dto_result['inspections'].append(temp_dict)

    print(dto_result)

    response = jsonify(dto_result)

    return response

def convert_to_serializable(obj):
    if isinstance(obj, np.generic):
        return obj.item()
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    
    return obj

# 여기에 모델 삽입해서 결함 종류 / 결함 범위 JSON으로 전달해주기
""" 
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Load image and analyze
        image = cv2.imread(filepath)
        results = analyze_image(image)  # 모델 분석 함수 호출

        return jsonify(results)

def analyze_image(image):
    # 여기서 모델을 사용하여 이미지를 분석
    # 예시로 임의의 결함 정보를 반환
    defects = [
        {"position": "top-left", "type": "scratch"},
        {"position": "bottom-right", "type": "crack"}
    ]
    return {"defects": defects}
"""
# 바이너리 파일 이미지 변화 함수
def binary_to_image(binary_data):
    image_stream = BytesIO(binary_data)

    image_array = np.frombuffer(image_stream.read(), dp = np.uint8)

    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    return image


# 서버 가동 확인용 경로
@app.route('/')
def home():
   return 'Tech-titans AI Server (Flask)'

# 문자열 전달 확인용 경로
@app.route('/receive_string', methods=['POST'])
def receive_string():
    print('문자열 받음')

    dto_json = request.get_json()

    if dto_json is None:
        return jsonify({"error": "No JSON data provided"}), 400

    value = dto_json.get('value') 
    print('Extracted value:', value)

    response = jsonify({"data": value + ' -from Flask-', "status": HTTPStatus.OK})
    print(response)
    print(response.data)
    return response

# main문
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
