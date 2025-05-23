import sys
import os

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_src_path = os.path.abspath(os.path.join(current_dir, "..", "src"))
sys.path.insert(0, project_src_path)

from onvif import ONVIFCamera, ONVIFService
from onvif.exceptions import ONVIFError
from structures import Position, Speed

from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QPushButton,
    QGridLayout,
)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
import cv2

from camera import Camera


class VideoCaptureWidget(QWidget):
    def __init__(
        self,
        cv_stream,
        parent=None,
        video_size=(1280, 960),
        connection_info=None,
        camera=None,
    ):
        super().__init__(parent)
        self.video_capture = cv_stream
        self.video_size = video_size
        self.connection_info = connection_info
        print("cam from video_widget:", camera)
        self.camera = camera

        if not self.video_capture.isOpened():
            print("Cannot open camera")
            return

        # Initialize UI components
        self.image_label = QLabel(self)
        self._setup_ui()

        # Set up video update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def _setup_ui(self):
        """Initialize user interface components"""
        main_layout = QVBoxLayout(self)

        # Video and info panel
        video_info_layout = QHBoxLayout()
        video_info_layout.addWidget(self.image_label)
        video_info_layout.addLayout(self._create_info_panel())

        # Add PTZ controls
        main_layout.addLayout(video_info_layout)
        main_layout.addLayout(self._create_ptz_controls())

    def _create_info_panel(self):
        """Create connection information panel"""
        info_layout = QFormLayout()
        if self.connection_info:
            info_layout.addRow("IP:", QLabel(self.connection_info.get("ip", "N/A")))
            info_layout.addRow("Port:", QLabel(self.connection_info.get("port", "N/A")))
            info_layout.addRow(
                "Login:", QLabel(self.connection_info.get("login", "N/A"))
            )
            info_layout.addRow("RTSP:", QLabel(self.connection_info.get("rtsp", "N/A")))
        return info_layout

    def _create_ptz_controls(self):
        """Create PTZ control buttons arranged in arrow pattern"""
        controls_layout = QGridLayout()

        # Create arrow buttons
        self.btn_up = QPushButton("↑", self)
        self.btn_down = QPushButton("↓", self)
        self.btn_left = QPushButton("←", self)
        self.btn_right = QPushButton("→", self)
        self.btn_zoom_closer = QPushButton("🔍+", self)
        self.btn_zoom_away = QPushButton("🔍-", self)

        # Style buttons
        for btn in [
            self.btn_up,
            self.btn_down,
            self.btn_left,
            self.btn_right,
            self.btn_zoom_closer,
            self.btn_zoom_away,
        ]:
            btn.setFixedSize(60, 40)
            btn.setStyleSheet("QPushButton {font-size: 20px;}")

        self.btn_home = QPushButton("⌂", self)
        self.btn_home.setFixedSize(60, 40)
        self.btn_home.clicked.connect(self._go_home)
        controls_layout.addWidget(self.btn_home, 1, 1)

        # Arrange buttons in grid
        controls_layout.addWidget(self.btn_up, 0, 1)
        controls_layout.addWidget(self.btn_left, 1, 0)
        controls_layout.addWidget(self.btn_right, 1, 2)
        controls_layout.addWidget(self.btn_down, 2, 1)
        controls_layout.addWidget(self.btn_zoom_closer, 1, 3)
        controls_layout.addWidget(self.btn_zoom_away, 2, 3)

        self.btn_up.pressed.connect(self._start_movement)
        self.btn_down.pressed.connect(self._start_movement)
        self.btn_left.pressed.connect(self._start_movement)
        self.btn_right.pressed.connect(self._start_movement)
        self.btn_zoom_away.pressed.connect(self._start_zoom)
        self.btn_zoom_closer.pressed.connect(self._start_zoom)

        self.btn_up.released.connect(self._stop_movement)
        self.btn_down.released.connect(self._stop_movement)
        self.btn_left.released.connect(self._stop_movement)
        self.btn_right.released.connect(self._stop_movement)
        self.btn_zoom_away.pressed.connect(self._stop_movement)
        self.btn_zoom_closer.pressed.connect(self._stop_movement)

        return controls_layout

    def _start_movement(self):
        sender = self.sender()

        if sender == self.btn_up:
            speed = Speed(x_speed=0.0, y_speed=1.0, zoom_speed=0.0)
        elif sender == self.btn_down:
            speed = Speed(x_speed=0.0, y_speed=-1.0, zoom_speed=0.0)
        elif sender == self.btn_left:
            speed = Speed(x_speed=-1.0, y_speed=0.0, zoom_speed=0.0)
        elif sender == self.btn_right:
            speed = Speed(x_speed=1.0, y_speed=0.0, zoom_speed=0.0)
        else:
            return

        if self.camera:
            try:
                print("self.camera:")
                print(self.camera.getDeviceInformation)
                self.camera.continiousMove(speed, method_is_blocking=False)
            except ONVIFError as e:
                print(f"PTZ Error: {str(e)}")

    def _start_zoom(self):
        sender = self.sender()

        if sender == self.btn_zoom_closer:
            speed = Speed(x_speed=0.0, y_speed=0.0, zoom_speed=1.0)
        elif sender == self.btn_zoom_away:
            speed = Speed(x_speed=0.0, y_speed=0.0, zoom_speed=-1.0)
        else:
            return

        if self.camera:
            try:
                self.camera.continiousMove(speed, method_is_blocking=False)
            except ONVIFError as e:
                print(f"PTZ Error: {str(e)}")

    # def _stop_zoom(self):
    #     """Handle button release events"""
    #     if self.camera:
    #         try:
    #             # Stop both pan/tilt and zoom
    #             self.camera.stop(stop_zoom=True)
    #         except ONVIFError as e:
    #             print(f"Stop Error: {str(e)}")

    def _stop_movement(self):
        """Handle button release events"""
        if self.camera:
            try:
                # Stop both pan/tilt and zoom
                self.camera.stop(stop_x_y=True, stop_zoom=True)
            except ONVIFError as e:
                print(f"Stop Error: {str(e)}")

    def _go_home(self):
        if self.camera:
            try:
                self.camera.gotoHomePosition()
            except ONVIFError as e:
                print(f"Home Position Error: {str(e)}")

    def update_frame(self):
        """Update video feed display"""
        ret, frame = self.video_capture.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            convert_to_Qt_format = QImage(frame.data, w, h, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(convert_to_Qt_format)
        self.image_label.setPixmap(pixmap.scaled(*self.video_size))

    def closeEvent(self, event):
        """Handle window close event"""
        self.timer.stop()
        self.video_capture.release()
        event.accept()
