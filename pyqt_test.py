from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtGui import QImage, QPixmap, QFont, QFontDatabase
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import sys
import cv2
import json
from segment_model import *

# 메인 화면 웹캠 화면 구성 위젯

class VideoCaptureWidget(QWidget):
    def __init__(self, photo_label, parent=None):
        super().__init__(parent)
        self.photo_label = photo_label

        # 웹캠 초기화
        self.cap = cv2.VideoCapture(0)

        # 타이머 설정 (30ms 간격으로 업데이트)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # 비디오 프레임을 표시할 QLabel
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setFixedHeight(400)

        # 레이아웃 설정
        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        self.setLayout(layout)

        # 포커스 정책 설정
        self.setFocusPolicy(Qt.StrongFocus)
        self.current_frame = None  # 현재 프레임 초기화

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
    
    # 특정 트리거를 통한 캡처 이벤트
    # 추후 컨베이어 벨트 센서 접촉시 촬영으로 변경 예정
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_C:
            self.capture_frame()

    # 이미지 촬영
    def capture_frame(self):
        if hasattr(self, 'current_frame'):
            # 캡처된 프레임을 RGB로 변환
            rgb_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)

            print("이미지 캡처 완료")
            # OpenCV 이미지를 분석
            img, results = predict_image_segment_file(rgb_frame)
            print("이미지 분석 완료")

            # 분석된 이미지를 QPixmap으로 변환
            cvt_img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            qpixmap_result = self.cv2_to_qpixmap(cvt_img)
            
            # QLabel에 표시할 Pixmap으로 설정
            self.photo_label.setPixmap(qpixmap_result)

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

# 메인 화면 구성
class MainPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        layout = QVBoxLayout()

        middle_layout = QHBoxLayout()

        # 실시간 촬영 사진 표시 공간
        self.photo_label = QLabel('캡처된 이미지\n YOLOv8을 통한 검출 사진', self)
        self.photo_label.setStyleSheet("background-color: lightgray; font-size: 16px; text-align: center;")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setFixedSize(600, 300)
        middle_layout.addWidget(self.photo_label)

        # 실시간 탐지 결과 표시 공간
        self.detect_label = QLabel('합 / 불 양품 검출', self)
        self.detect_label.setStyleSheet("background-color: white; font-size: 20px; font-weight: bold; text-align: center; border: 1px solid black;")
        self.detect_label.setAlignment(Qt.AlignCenter)
        self.detect_label.setFixedSize(600, 300)
        middle_layout.addWidget(self.detect_label)

        # 비디오 캡처 위젯 추가
        self.video_widget = VideoCaptureWidget(self.photo_label, self)

        layout.addWidget(self.video_widget)
        layout.addLayout(middle_layout)

        bottom_layout = QHBoxLayout()

        # 종료 버튼
        self.exit_button = QPushButton('프로그램 종료', self)
        self.exit_button.setStyleSheet("background-color: gray; font-size: 24px; font-weight: bold; color: white; border-radius: 5px;")
        self.exit_button.setFixedSize(200, 70)
        self.exit_button.clicked.connect(parent.close_application)
        bottom_layout.addWidget(self.exit_button)

        bottom_layout.addStretch()

        # 상태 관리 버튼
        self.status_button = QPushButton('상태 관리', self)
        self.status_button.setStyleSheet("background-color: green; font-size: 24px; font-weight: bold; color: white; border-radius: 5px;")
        self.status_button.setFixedSize(200, 70)
        self.status_button.clicked.connect(parent.show_status)
        bottom_layout.addWidget(self.status_button)

        # 긴급 버튼
        self.stop_button = QPushButton('긴급 버튼', self)
        self.stop_button.setStyleSheet("background-color: red; font-size: 24px; font-weight: bold; color: white; border-radius: 5px;")
        self.stop_button.setFixedSize(200, 70)
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

# 통계 화면 구성
class StatusPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()

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
        label.setStyleSheet("font-size: 36px; color: black; font-weight: bold; padding-top : 15px")
        label.setFixedHeight(70)
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(label, row, col, 1, colspan)

        value = QLabel(value_text, self)
        value.setStyleSheet(
            "font-size: 40px; color: black; border: 1px solid #CACACA; border-radius: 15px; font-weight: bold;" 
            if label_text != '결함 비율' 
            else "font-size: 36px; color: black; border: 1px solid #CACACA; border-radius: 15px; font-weight: bold;"
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
        # 서버에서 받은 데이터로 상태 페이지 업데이트
        self.defect_rate_value.setText(data["defect_rate"])
        self.defect_count_value.setText(data["defect_count"])
        self.defect_ratio_value.setText("\n".join([f"{k} : {v}" for k, v in data["defect_ratio"].items()]))
        self.production_value.setText(data["production"])

# 화면 이외의 메소드들
class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PyQt5 Layout Example')
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 1600, 900)
        self.setStyleSheet("background-color: #2c2e3e;")

        self.stacked_widget = QStackedWidget()
        self.main_page = MainPage(self)
        self.status_page = StatusPage(self)
        self.stacked_widget.addWidget(self.main_page)
        self.stacked_widget.addWidget(self.status_page)

        layout = QVBoxLayout()
        layout.addWidget(self.stacked_widget)
        self.setLayout(layout)

        # DB연결 후 주석 해제
        # self.network_manager = QNetworkAccessManager()
        # self.network_manager.finished.connect(self.on_data_received)

        self.show()

    def show_status(self):
        # 상태 관리 페이지 표시
        self.stacked_widget.setCurrentWidget(self.status_page)

        # DB연결 후 주석 해제
        # self.fetch_data()

    def go_back(self):
        # 메인 페이지로 돌아가기
        self.stacked_widget.setCurrentIndex(0)
        self.main_page.focus_video_widget()  # 비디오 위젯에 포커스 설정
    
    # 아직은 서버에서 fetch 금지
    # 나중에 db서버와 연결할 예정

    '''
    def fetch_data(self):
        # 서버에서 데이터 요청
        url = QUrl("http://example.com/data")  # 실제 서버 URL로 변경 필요
        request = QNetworkRequest(url)
        self.network_manager.get(request)

    def on_data_received(self, reply):
        # 서버에서 데이터 수신 후 처리
        er = reply.error()
        if er == QNetworkReply.NoError:
            bytes_string = reply.readAll()
            json_data = json.loads(str(bytes_string, 'utf-8'))
            self.status_page.update_status_page(json_data)
        else:
            print("Error occurred: ", er)
            print(reply.errorString())
    '''
    def close_application(self):
        # 애플리케이션 종료
        self.close()
        sys.exit(0)

    def emergency_stop(self):
        # 긴급 멈춤 팝업창
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
            # 재작동 메시지 표시
            QMessageBox.information(self, "재작동", "컨베이어 벨트가 재작동합니다!")

    def closeEvent(self, event):
        # 메인 페이지의 리소스 해제
        self.main_page.closeEvent(event)
        sys.exit(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 폰트 DB 생성 및 앱 내 폰트 적용
    fontDB = QFontDatabase()
    font_id = fontDB.addApplicationFont('Noto_Sans_KR/NotoSansKR-VariableFont_wght.ttf')
    if font_id == -1:
        print("폰트 로딩 실패")
    else:
        print("폰트 로딩 성공")

    # 폰트 적용
    app.setFont(QFont('Noto Sans KR'))
    ex = MyApp()
    sys.exit(app.exec_())
