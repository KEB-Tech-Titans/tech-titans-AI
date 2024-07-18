import cv2
import numpy as np
import matplotlib.pyplot as plt
from ultralytics import YOLO

model_box = YOLO('model_box.pt')
model_segment = YOLO('segement_model_ephocs_30.pt')

# 이미지 리사이징을 위함
# 추후 최적의 리사이징 크기 찾을시 변경 가능
img_size = 640

# 이미지 분석 코드
# 이미지 분석 코드 -> image file path 혹은 image file 자체를 받는 것을 생각

# segment 활용하여 area 크기 구하는 코드입니다
def predict_image_segment(image_path):
    predict_image = cv2.imread(image_path)

    resized_pred_img = image_resize(img_size, predict_image)

    results = model_segment(resized_pred_img, task='segment')

    created_img, pred_result = create_segement_area(results, resized_pred_img)

    # 이미지 시각화
    # debug code -> 추후 삭제
    plt.figure(figsize=(10, 10))
    plt.imshow(created_img)
    plt.axis('off')
    plt.title('YOLOv8 Segmentation')
    plt.show()

    # pred_result -> json형식으로 변환후 spring 서버로 보낼 예정
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
        confs = results[0].boxes.cls.cpu().numpy()

        for i, mask in enumerate(masks):
            # Mask를 바이너리 이미지로 변환
            mask_binary = (mask > 0.5).astype(np.uint8)  # 바이너리 이미지로 변환

            # 마스크의 픽셀 개수를 세서 넓이 계산
            area = np.sum(mask_binary)

            # spring server로 보낼 내용 정리
            result_dict = {}
            class_id = int(cls_ids[i])
            result_dict['class'] = classes[cls_ids[i]]
            result_dict['conf'] = confs[i]
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

        return [img, result_array]
    else:
        print("No mask in the image")
        return [img, {'msg' : 'No mask in image'}]

# 바운딩 박 스테 스트용 코드 -> 쓸일 없을듯
# 바운딩 박스 그리는 코드입니다
def predict_image_box(image_path):
    predict_image = cv2.imread(image_path)

    results = model_box(predict_image)

    # 분석 완료 후 바운딩 박스가 그려진 이미지    
    created_img, result_dict = create_bounding_box(results, predict_image)

    # # 결과 이미지를 화면에 표시
    # img_rgb = cv2.cvtColor(created_img, cv2.COLOR_BGR2RGB)
    # img_pil = Image.fromarray(img_rgb)
    # img_pil.show()

    print(f'image predict result : {result_dict}')

# 일단 임시로 바운딩 박스 정보를 출력
def create_bounding_box(results, img):
    result_dict = []

    # 이미지에 각 감지된 객체의 바운딩 박스를 그립니다.
    for result in results:
        for box in result.boxes:
            # 박스를 그릴 4개의 꼭짓점 좌표를 구한다
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            # 인식된 객체가 어느 정도 확률로 객체가 맞을까?
            conf = box.conf.item()

            # 클래스 번호(예를들어 0 => 스마트폰)
            cls = box.cls.item()
            box_info = {}
            if conf > 0.5:
                # 웹 서버로 보낼 박스 정보 dictionary만들기
                box_info['cls'] = model_box.names[int(cls)]
                box_info['conf'] = f'{conf:.2f}'
                box_info['area'] = f'{(x2 - x1) * (y2 - y1):.3f}'
                
                # log
                print(f'Detected box result : {box_info}')

                result_dict.append(box_info)

                # 바운딩 박스를 이미지에 그림
                cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                label = f'{model_box.names[int(cls)]} {conf:.2f}'
                cv2.putText(img, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return [img, result_dict]


# 임시 테스트용
# predict_image_box('Scr_0008.png')
predict_image_segment('Scr_0008.png')