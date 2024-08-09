# 인텔 cpu에서 간헐적으로 실행이 안되는 문제
# 환경 변수 설정 풀어야 lib뭐시기 오류 해결 가능합니다
# 나중에 메인으로 실행하는 프로그램으로 코드 옮길 예정
import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'

import cv2
import numpy as np
import matplotlib.pyplot as plt
from ultralytics import YOLO

if os.name == 'nt':
    # model_segment = YOLO('..\\ai_model\\segment_model_20240725.pt')
    model_segment = YOLO('C:\\0.git\\tech-titans-AI\\ai_model\\segment_model_20240725.pt')
    # model_segment = YOLO('tech_titan\\tech-titans-AI\\ai_model\\segment_model_20240725.pt')
else:
    model_segment = YOLO('../ai_model/segment_model_20240725.pt')
# 이미지 리사이징을 위함
# 추후 최적의 리사이징 크기 찾을시 변경 가능
img_size = 640

# 이미지 분석 코드
# 이미지 분석 코드 -> image file path 혹은 image file 자체를 받는 것을 생각
# 이미지 파일 자체를 받아서 이미지를 예측
def predict_image_segment_file(image):
    # 파일 객체로부터 이미지 데이터 읽기
    predict_image = image

    # 이미지 사이즈 조정 및 예측
    resized_pred_img = image_resize(img_size, predict_image)
    results = model_segment(resized_pred_img, task='segment')

    # 세그먼테이션 영역 생성 및 결과 처리
    created_img, pred_result = create_segement_area(results, resized_pred_img)

    # 이미지 시각화 (디버그 코드, 추후 삭제)
    # plt.figure(figsize=(10, 10))
    # plt.imshow(created_img)
    # plt.axis('off')
    # plt.title('YOLOv8 Segmentation')
    # plt.show()

    # 예측 결과 JSON 형식으로 변환 후 Spring 서버로 전송 예정
    print(f'Predict result : {pred_result}')

    return created_img, pred_result


# 이미지 리사이징 코드
def image_resize(size, img):
    width = size
    height = int(size * (1080/1920))

    # opencv 활용 이미지 변환
    resized_img = cv2.resize(img, (width, height))

    resized_img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)

    return resized_img
    
# segment를 통해 얻어낸 영역을 구하는 코드
def create_segement_area(results, img):
    result_array = []

    # 감지된 객체들에 대한 정보를 프레임에 표시 및 넓이 계산
    if results and results[0].masks is not None:
        masks = results[0].masks.data.cpu().numpy()  # 모든 마스크 데이터를 NumPy 배열로 변환
        cls_ids = results[0].boxes.cls.cpu().numpy()  # 각 객체의 클래스 ID를 가져옴
        classes = results[0].names  # 클래스 이름을 얻음
        confs = results[0].boxes.conf.cpu().numpy()
        
        for i, mask in enumerate(masks):
            # Mask를 바이너리 이미지로 변환
            mask_binary = (mask > 0.5).astype(np.uint8)  # 바이너리 이미지로 변환

            # 마스크의 픽셀 개수를 세서 넓이 계산
            area = np.sum(mask_binary)

            # spring server로 보낼 내용 정리
            result_dict = {}
            class_id = int(cls_ids[i])
            result_dict['class'] = classes[cls_ids[i]]
            result_dict['conf'] = f"{confs[i]:.3f}"
            result_dict['area'] = area

            result_array.append(result_dict)

            # 마스크의 컨투어 찾기
            contours, _ = cv2.findContours(mask_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)
            
            # 외곽선 그리기
            for contour in contours:
                cv2.drawContours(img, [contour], -1, (0, 255, 0), 1)

            # 클래스 라벨링 추가
            if contours:
                x, y, w, h = cv2.boundingRect(contours[0])
                class_id = int(cls_ids[i])
                class_label = classes[class_id]
                cv2.putText(img, f'{class_label}', (int(x), int(y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        if not contains_single_smartphone(result_array):
            result_array.append({'condition' : 'fail'})
        else:
            if contains_no_oil_stain_scratch(result_array):
                result_array.append({'condition' : 'pass'})
            else:
                result_array.append({'condition' : 'fail'})

        return [img, result_array]
    else:
        print("No mask in the image")
        return [img, {'msg' : 'No mask in image'}]
    
def contains_single_smartphone(result_array):
    smartphone_count = sum(1 for result_dict in result_array if result_dict.get('class') == 'smartphone')
    return smartphone_count == 1

def contains_no_oil_stain_scratch(result_array):
    unwanted_classes = {'oil', 'stain', 'scratch'}
    return not any(result_dict.get('class') in unwanted_classes for result_dict in result_array)