# video_capture_widget.py
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
import cv2


class VideoCaptureWidget(QWidget):
    def __init__(self, cv_stream, parent=None):
        super().__init__(parent)

        self.video_capture = cv_stream
        if not self.video_capture.isOpened():
            print("Cannot open camera")
            return

        self.image_label = QLabel(self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.image_label)

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
            resized_pixmap = pixmap.scaled(self.image_label.width(), self.image_label.height())
            self.image_label.setPixmap(resized_pixmap)

    def closeEvent(self, event):
        self.timer.stop()
        self.video_capture.release()
        event.accept()

