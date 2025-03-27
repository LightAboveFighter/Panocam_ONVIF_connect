import sys
import cv2
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer

from camera import Camera

class VideoCaptureWidget(QWidget):
    def __init__(self, stream):
        super().__init__()

        self.video_capture = stream
        if not self.video_capture.isOpened():
            print("Cannot open camera")
            exit()

        self.image_label = QLabel(self)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.image_label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(60)


    def update_frame(self):
        ret, frame = self.video_capture.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

            pixmap = QPixmap.fromImage(q_image)
            self.image_label.setPixmap(pixmap)



    def closeEvent(self, event):
        self.timer.stop()
        self.video_capture.release()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoCaptureWidget()
    window.setWindowTitle("Video Capture")
    window.show()
    sys.exit(app.exec())
