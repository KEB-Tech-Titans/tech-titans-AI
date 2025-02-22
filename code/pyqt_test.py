from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QFont, QFontDatabase
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import sys
import cv2
import math
import threading
import time

from segment_model import *
from db_connection import *
from db_instance import *

import fileOperation
import db_connection, db_instance
import serial_connect  # serial_connect 모듈 임포트

# db_connection
conn = ''

def calc_defect_severity(segments):
    # 스마트폰 면적 추출 
    smartphone_area_list = [segment['area'] for segment in segments if segment.get('class') == 'smartphone']
    if len(smartphone_area_list) == 0:
        return -1
    
    smartphone_area = smartphone_area_list[0]

    defect_areas = {}
    for segment in segments:
        # smaprtphone은 결함이 아니니 예외처리
        if 'class' not in segment or segment['class'] == 'smartphone':
            continue

        if 'class' not in segment or segment['class'] == 'speaker':
            continue

        if 'class' not in segment or segment['class'] == 'button':
            continue

        if 'class' not in segment or segment['class'] == 'camera':
            continue

        # defect_area에 클래스가 없는 경우 .0으로 초기화
        if segment['class'] not in defect_areas:
            defect_areas[segment['class']] = .0
        
        # 해당 클래스의 결함 면적을 추가
        defect_areas[segment['class']] += segment['area']

    # 결함의 개수가 0이라면 바로 return 0
    if len(defect_areas) == 0:
        return 0
    
    # 스마트폰 면적 대비 결함의 크기 계산
    defect_rates = {}
    for defect_class, area in defect_areas.items():
        if area > smartphone_area:
            return -1

        defect_rates[defect_class] = area / smartphone_area
    
    # 결함별 계수, 임시값이므로 직접 측정하여 조정 필요
    defect_coef = {'oil': 5, 'stain': 10, 'scratch': 30}
    defect_severity = 0.0
    for defect_class, rate in defect_rates.items():
        # 결함율이 조금만 커져도 지수적으로 증가
        severity = (math.e ** (defect_coef[defect_class] * rate) - 1)
        # print(severity)
        defect_severity += severity

        if defect_severity >= 100:
            return 100

    return defect_severity


# 메인 화면 웹캠 화면 구성 위젯
class VideoCaptureWidget(QWidget):
    def __init__(self, photo_label, parent=None):
        super().__init__(parent)
        self.photo_label = photo_label

        # 화면 해상도 가져오기
        desktop = QApplication.desktop()
        screen_rect = desktop.screenGeometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()

        # 웹캠 초기화
        # 다른 웹캠 연결시 VideoCapture번호 바꾸기
        self.cap = cv2.VideoCapture(1)


        # 타이머 설정 (30ms 간격으로 업데이트)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # 비디오 프레임을 표시할 QLabel
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setFixedSize(int(screen_width * 0.6), int(screen_height * 0.6))  # 해상도에 따라 크기 조정

        # 레이아웃 설정
        layout = QVBoxLayout()
        
        # 위와 아래에 빈 공간 추가하여 가운데 정렬
        layout.addStretch()
        layout.addWidget(self.video_label, alignment=Qt.AlignCenter)
        layout.addStretch()
        
        self.setLayout(layout)

        # 포커스 정책 설정
        self.setFocusPolicy(Qt.StrongFocus)
        self.current_frame = None  # 현재 프레임 초기화

        self.conveyor_thread = threading.Thread(target=self.conveyor_sensor_event)
        self.conveyor_thread.daemon = True  # 메인 스레드 종료 시 이 스레드도 종료
        self.conveyor_thread.start()

        self.passed_signal = pyqtSignal(bool, name='passed_signal')

        self.is_passed = None
    def update_frame(self):
        # 웹캠에서 프레임 읽기 및 QLabel 업데이트
        ret, frame = self.cap.read()
        if ret:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(qt_image))
            self.current_frame = frame  # 현재 프레임 저장
    
    def conveyor_sensor_event(self):
        while True:  # 이 루프는 데이터를 계속해서 수신하려는 경우 사용
            received_data = serial_connect.receive_command(serial_connect.conveyor_ser, "Captured Frame")
            if received_data == "Captured Frame":
                self.capture_frame()
            # 추가 조건이 필요하면 여기에서 추가적으로 처리 가능
            time.sleep(1)  # 너무 빈번한 수신을 방지하기 위해 잠시 대기 (필요에 따라 조정 가능)

    # 특정 트리거를 통한 캡처 이벤트
    # 추후 컨베이어 벨트 센서 접촉시 촬영으로 변경 예정
    # def keyPressEvent(self, event):
    #     if event.key() == Qt.Key_C:
    #         self.capture_frame()

    # 이미지 촬영
    def capture_frame(self):
        if hasattr(self, 'current_frame'):
            # 캡처된 프레임을 RGB로 변환
            rgb_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            print("이미지 캡처 완료")
            # RGB 프레임을 파일로 저장 (예: 'captured_image.png')
            raw_file_name, raw_date_time = fileOperation.make_raw_file_name(True)
            cv2.imwrite(raw_file_name, cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR))
            fileOperation.upload_to_s3(raw_file_name, raw_date_time)
            fileOperation.save_file_info_to_raw_file_table(raw_file_name, raw_date_time)
            os.remove(raw_file_name)
            
            # OpenCV 이미지를 분석
            img, results = predict_image_segment_file(rgb_frame)
            print(results)
            if 'msg' in results and results['msg'] == {'msg': 'No mask in image'}:
                print('No mask in image')
                while True: 
                    if serial_connect.receive_command(serial_connect.conveyor_ser, "Waiting process...") == "Waiting process...":
                        break
                serial_connect.send_command(serial_connect.conveyor_ser, "end")
                serial_connect.send_command(serial_connect.motor_ser, "fail")
                return
                # fail 처리하고 return 해주세요
            # 분석결과!!
            if (results): 
                self.is_passed = False
            else:
                result = results[len(results) - 1]
                # 분석결과 양품 불량품 판정
                if result['condition'] == 'pass':
                    self.is_passed = True
                else:
                    self.is_passed = False

            self.passed_signal.emit(self.is_passed)

            # 분석된 결과 db 및 s3 내부에 저장
            analyzed_file_name, analyzed_date_time = fileOperation.make_raw_file_name(False)
            cv2.imwrite(analyzed_file_name, img)
            fileOperation.upload_to_s3(analyzed_file_name, analyzed_date_time)
        
            defect_severity = calc_defect_severity(results)
            print(defect_severity)

            fileOperation.save_file_info_to_analyzed_file_table(analyzed_file_name, analyzed_date_time, self.is_passed, raw_file_name, defect_severity)

            # inspection DB에 들어가는 정보를 저장
            all_defect = ['oil', 'scratch', 'stain']
            inspections = []    # 이거 DB에 파싱해서 넣으시면 됩니다
            for result in results:
                try:
                    if result['class'] in all_defect:
                        inspections.append(result)
                except:
                    break
            print(f'inspections : {inspections}')

            defect_type_mapping = {
                'oil': 0,
                'scratch': 1,
                'stain': 2
            }

            for inspection in inspections:
                print(inspection)
                defect_type_value = defect_type_mapping.get(inspection['class'], -1)  # 만약 매핑되지 않는 값이 들어올 경우 -1로 설정
                new_inspection = db_instance.Inspection(
                    created_at = analyzed_date_time,
                    updated_at = analyzed_date_time,
                    analyzed_file_name = analyzed_file_name,
                    area = inspection['area'],
                    defect_type = defect_type_value,
                )
                db_connection.insert_inspection_data(new_inspection, db_connection.connect_mysql())
                print("inspection 테이블에 저장완료")
            os.remove(analyzed_file_name)

            # 분석된 이미지를 QPixmap으로 변환
            cvt_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            qpixmap_result = self.cv2_to_qpixmap(cvt_img)
            
            # QLabel에 표시할 Pixmap으로 설정
            self.photo_label.setPixmap(qpixmap_result)

            # 아두이노 모터에 결과 전송!!!!!!!

            # 분석 결과에 따라 pass 또는 fail 명령 전송
            if self.is_passed:  # 실제로 pass 조건을 결정하는 로직으로 수정 필요
                print("product is safe!!")
                while True: 
                    if serial_connect.receive_command(serial_connect.conveyor_ser, "Waiting process...") == "Waiting process...":
                        break
                serial_connect.send_command(serial_connect.conveyor_ser, "end")
                serial_connect.send_command(serial_connect.motor_ser, "pass")
            else:
                print('product is unsafe!!')
                while True: 
                    if serial_connect.receive_command(serial_connect.conveyor_ser, "Waiting process...") == "Waiting process...":
                        break
                serial_connect.send_command(serial_connect.conveyor_ser, "end")
                serial_connect.send_command(serial_connect.motor_ser, "fail")

    def cv2_to_qpixmap(self, cv2_image):
        '''OpenCV 이미지를 QPixmap으로 변환'''
        height, width, channel = cv2_image.shape
        bytes_per_line = channel * width
        # QImage로 변환 (RGB 포맷 사용)
        qimage = QImage(cv2_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        # QPixmap으로 변환
        qpixmap = QPixmap.fromImage(qimage)
        return qpixmap

    def closeEvent(self, event):
        # 타이머 정지 및 웹캠 해제
        self.timer.stop()
        self.cap.release()
        serial_connect.conveyor_ser.close()  # 시리얼 포트 닫기
        serial_connect.motor_ser.close()

# 메인 화면 구성
class MainPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        # 화면 해상도 가져오기
        desktop = QApplication.desktop()
        screen_rect = desktop.screenGeometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()

        layout = QVBoxLayout()

        middle_layout = QHBoxLayout()

        # 실시간 촬영 사진 표시 공간
        self.photo_label = QLabel('캡처된 이미지\n YOLOv8을 통한 검출 사진', self)
        self.photo_label.setStyleSheet("background-color: lightgray; font-size: 16px; text-align: center;")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setFixedSize(int(screen_width * 0.3), int(screen_height * 0.3))  # 해상도에 따라 크기 조정
        middle_layout.addWidget(self.photo_label)

        # 실시간 탐지 결과 표시 공간
        self.detect_label = QLabel(self)
        self.detect_label.setStyleSheet("background-color: lightgray; font-size: 64px; font-weight: bold; text-align: center; border: 1px solid black;")
        self.detect_label.setAlignment(Qt.AlignCenter)
        self.detect_label.setFixedSize(int(screen_width * 0.3), int(screen_height * 0.3))  # 해상도에 따라 크기 조정
        middle_layout.addWidget(self.detect_label)

        # 비디오 캡처 위젯 추가
        self.video_widget = VideoCaptureWidget(self.photo_label, self)

        self.video_widget.passed_signal.connect(self.update_detect_label)

        

        layout.addWidget(self.video_widget)
        layout.addLayout(middle_layout)

        bottom_layout = QHBoxLayout()

        # 종료 버튼
        self.exit_button = QPushButton('프로그램 종료', self)
        self.exit_button.setStyleSheet("background-color: gray; font-size: 24px; font-weight: bold; color: white; border-radius: 5px;")
        self.exit_button.setFixedSize(int(screen_width * 0.1), int(screen_height * 0.05))  # 해상도에 따라 크기 조정
        self.exit_button.clicked.connect(parent.close_application)
        bottom_layout.addWidget(self.exit_button)

        bottom_layout.addStretch()

        # 상태 관리 버튼
        self.status_button = QPushButton('상태 관리', self)
        self.status_button.setStyleSheet("background-color: green; font-size: 24px; font-weight: bold; color: white; border-radius: 5px;")
        self.status_button.setFixedSize(int(screen_width * 0.1), int(screen_height * 0.05))  # 해상도에 따라 크기 조정
        self.status_button.clicked.connect(parent.show_status)
        bottom_layout.addWidget(self.status_button)

        # 긴급 버튼
        self.stop_button = QPushButton('긴급 버튼', self)
        self.stop_button.setStyleSheet("background-color: red; font-size: 24px; font-weight: bold; color: white; border-radius: 5px;")
        self.stop_button.setFixedSize(int(screen_width * 0.1), int(screen_height * 0.05))  # 해상도에 따라 크기 조정
        self.stop_button.clicked.connect(parent.emergency_stop)
        bottom_layout.addWidget(self.stop_button)

        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    def closeEvent(self, event):
        # 비디오 캡처 위젯의 리소스 해제
        self.video_widget.closeEvent(event)

    def focus_video_widget(self):
        # 비디오 위젯에 포커스 설정
        self.video_widget.setFocus()
    def updated_detect_label(self, is_passed):
        if is_passed is None:
            self.detect_label.setText('합/불 양품 판정')
            self.detect_label.setStyleSheet(
                "background-color: lightgray; font-size: 64px; font-weight: bold; text-align: center; border: 1px solid black; color: blue;"
            )
        elif is_passed:
            self.detect_label.setText('합격')
            self.detect_label.setStyleSheet(
                "background-color: lightgray; font-size: 64px; font-weight: bold; text-align: center; border: 1px solid black; color: blue;"
            )
        else:
            self.detect_label.setText('불합격')
            self.detect_label.setStyleSheet(
                "background-color: lightgray; font-size: 64px; font-weight: bold; text-align: center; border: 1px solid black; color: red;"
            )
# 통계 화면 구성
class StatusPage(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()

        self.defect_type = ['Oil', 'Scratch', 'Stain']

        # 상태 관리 페이지 제목
        title = QLabel('12시간 이내 상태 관리 데이터', self)
        title.setStyleSheet("font-size: 32px; color: white; font-weight:bold;")
        title.setFixedHeight(70)
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(title)

        # 통계 레이아웃 설정
        stats_widget = QWidget(self)
        stats_layout = QGridLayout()
        stats_widget.setStyleSheet(
            "background-color: white;"
        )
        stats_widget.setLayout(stats_layout)
        # 통계 레이블 추가
        self.create_stat_label(stats_layout, '불량률', '3%', 0, 0)
        self.create_stat_label(stats_layout, '불량 발생 건수', '10건', 0, 1)
        self.create_stat_label(stats_layout, '결함 비율', 'Oil : 25%\tStain : 25%\nScratch : 25%\tBlack Spot : 25%', 2, 0)
        self.create_stat_label(stats_layout, '생산량', '1234개', 2, 1)
        layout.addWidget(stats_widget)

        bottom_layout = QHBoxLayout()

        # 프로그램 종료 버튼
        self.exit_button = QPushButton('프로그램 종료', self)
        self.exit_button.setStyleSheet("background-color: gray; font-size: 24px; font-weight: bold; color: white; border-radius: 5px;")
        self.exit_button.setFixedSize(200, 70)
        self.exit_button.clicked.connect(parent.close_application)
        bottom_layout.addWidget(self.exit_button)

        bottom_layout.addStretch()

        # 돌아가기 버튼
        self.back_button = QPushButton('돌아가기', self)
        self.back_button.setStyleSheet("background-color: green; font-size: 24px; font-weight: bold; color: white; border-radius: 5px;")
        self.back_button.setFixedSize(200, 70)
        self.back_button.clicked.connect(parent.go_back)
        bottom_layout.addWidget(self.back_button)

        # 긴급 버튼
        self.emergency_button = QPushButton('긴급 버튼', self)
        self.emergency_button.setStyleSheet("background-color: red; font-size: 24px; font-weight: bold; color: white; border-radius: 5px;")
        self.emergency_button.setFixedSize(200, 70)
        bottom_layout.addWidget(self.emergency_button)

        layout.addLayout(bottom_layout)
        self.setLayout(layout)

    def create_stat_label(self, layout, label_text, value_text, row, col, rowspan=1, colspan=1):
        # 통계 레이블과 값을 생성하여 레이아웃에 추가
        label = QLabel(label_text, self)
        label.setStyleSheet("font-size: 64px; color: black; font-weight: bold; padding-top : 15px")
        label.setFixedHeight(70)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(label, row, col, 1, colspan)

        value = QLabel(value_text, self)
        value.setStyleSheet(
            "font-size: 68px; color: black; border: 1px solid #CACACA; border-radius: 15px; font-weight: bold;" 
            if label_text != '결함 비율' 
            else "font-size: 64px; color: black; border: 1px solid #CACACA; border-radius: 15px; font-weight: bold;"
        )
        value.setAlignment(
            Qt.AlignCenter
            if label_text != '결함 비율'
            else Qt.AlignCenter | Qt.AlignLeft
        )
        layout.addWidget(value, row + 1, col, rowspan, colspan)

        # 각 통계 항목에 대한 레퍼런스를 저장
        if label_text == '불량률':
            self.defect_rate_value = value
        elif label_text == '불량 발생 건수':
            self.defect_count_value = value
        elif label_text == '결함 비율':
            self.defect_ratio_value = value
        elif label_text == '생산량':
            self.production_value = value

    # 추후 DB연결 시 바뀔 예정 있음
    def update_status_page(self, data):
        self.defect_rate_value.setText(data["defect_rate"])
        self.defect_count_value.setText(data["defect_count"])
        self.defect_ratio_value.setText("\n".join([f"{self.defect_type[k]} : {v}건" for k, v in data["inspection_count"].items()]))
        self.production_value.setText(data["production"])

    def fetch_and_update_data(self, conn):
        total_production = select_all_count(conn)
        defect_count = select_all_inspection_count(conn)
        inspection_count = select_defect_count(conn)
        

        # inspection count 정리
        for key in range(len(self.defect_type)):  # 0, 1, 2의 키를 확인
            if key not in inspection_count:
                inspection_count[key] = 0

        defect_rate = f"{(defect_count / total_production) * 100:.2f}%" if total_production else "0%"

        data = {
            "defect_rate": defect_rate,
            "defect_count": f"{defect_count}건",
            "inspection_count": inspection_count,
            "production": f"{total_production}개"
        }

        self.update_status_page(data)

# 화면 이외의 메소드들
class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PyQt5 Layout Example')
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: #2c2e3e;")

        self.stacked_widget = QStackedWidget()
        self.main_page = MainPage(self)
        self.status_page = StatusPage(self)
        self.stacked_widget.addWidget(self.main_page)
        self.stacked_widget.addWidget(self.status_page)

        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        self.conn = connect_mysql()

        self.showFullScreen()

    def show_status(self):
        self.stacked_widget.setCurrentWidget(self.status_page)
        if self.conn:
            self.status_page.fetch_and_update_data(self.conn)
        else:
            print('DB 연결 실패')

    def go_back(self):
        self.stacked_widget.setCurrentIndex(0)
        self.main_page.focus_video_widget() 

    def close_application(self):
        self.close()
        sys.exit(0)

    def emergency_stop(self):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("긴급 멈춤")
        msg_box.setText("컨베이어 벨트가 멈췄습니다!")
        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        ok_button = msg_box.button(QMessageBox.Ok)
        ok_button.setText("재작동")
        cancel_button = msg_box.button(QMessageBox.Cancel)
        cancel_button.setText("취소")

        msg_box.exec_()

        if msg_box.clickedButton() == ok_button:
            QMessageBox.information(self, "재작동", "컨베이어 벨트가 재작동합니다!")

    def closeEvent(self, event):
        self.main_page.closeEvent(event)
        sys.exit(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # mysql DB 접근
    conn = connect_mysql()
    if conn:
        print('DB 연결 성공')
    else:
        print('DB 연결 실패')

    # 폰트 DB 생성 및 앱 내 폰트 적용
    fontDB = QFontDatabase()
    font_id = fontDB.addApplicationFont('Noto_Sans_KR/NotoSansKR-VariableFont_wght.ttf')
    if font_id == -1:
        print("폰트 로딩 성공")
    else:
        print("폰트 로딩 실패")

    # 폰트 적용
    app.setFont(QFont('Noto Sans KR'))
    ex = MyApp()
    sys.exit(app.exec_())
