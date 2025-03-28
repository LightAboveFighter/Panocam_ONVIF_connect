# video_capture_widget.py
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFormLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
import cv2


class VideoCaptureWidget(QWidget):
    def __init__(self, cv_stream, parent=None, video_size=(640, 480), connection_info=None):
        super().__init__(parent)

        self.video_capture = cv_stream
        self.video_size = video_size
        self.connection_info = connection_info
        if not self.video_capture.isOpened():
            print("Cannot open camera")
            return

        self.image_label = QLabel(self)
        main_layout = QVBoxLayout(self)
        video_layout = QHBoxLayout()
        video_layout.addWidget(self.image_label)
        info_layout = QFormLayout()

        if self.connection_info:
            info_layout.addRow("IP:", QLabel(self.connection_info.get("ip", "N/A")))
            info_layout.addRow("Port:", QLabel(self.connection_info.get("port", "N/A")))
            info_layout.addRow("Login:", QLabel(self.connection_info.get("login", "N/A")))
            info_layout.addRow("RTSP:", QLabel(self.connection_info.get("rtsp", "N/A")))

        video_layout.addLayout(info_layout)
        main_layout.addLayout(video_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.video_capture.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(convert_to_Qt_format)
            # resized_pixmap = pixmap.scaled(self.image_label.width(), self.image_label.height())
            resized_pixmap = pixmap.scaled(self.video_size[0], self.video_size[1])
            self.image_label.setPixmap(resized_pixmap)
            self.image_label.setFixedSize(self.video_size[0], self.video_size[1])

    def closeEvent(self, event):
        self.timer.stop()
        self.video_capture.release()
        event.accept()

