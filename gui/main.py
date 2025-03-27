import sys
sys.path.insert(1, 'C:/Users/aggz1/MPTI Informatics/Sesestr4/cringeprak/Panocam_ONVIF_connect/src')
import json

from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtWidgets import QFileDialog

import main_window as main_window
import dialog_window as dialog_window
import text_window as text_window
from camera import Camera
from video_window import VideoCaptureWidget


class UserInput(QtWidgets.QMainWindow, text_window.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.connect_user_input)
    
    def connect_user_input(self):
        login = self.textEdit.toPlainText()
        password = self.textEdit_2.toPlainText()
        port = self.textEdit_3.toPlainText()
        ip = self.textEdit_4.toPlainText()
        
        # try:
        #     cam = Camera(ip, port, login, password)
        #     print("Connection successful")
        #     # cam.see_video('rtsp://falt:panofalt1234@77.232.155.123:556')
        #     video_window = cam.VideoCaptureWidget(cam.get_video_stream('rtsp://falt:panofalt1234@77.232.155.123:556'))
        #     video_window.show()
        # except:
        #     print("Connection error")


class CameraDialog(QtWidgets.QMainWindow, dialog_window.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushButton_1.clicked.connect(self.connect_with_config)
        self.pushButton_2.clicked.connect(self.show_user_input)
    
    def show_user_input(self):
        self.text_window = UserInput()
        self.text_window.show()
    
    def connect_with_config(self):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.AnyFile)
        filepath, _ = dialog.getOpenFileName()
        print("Opened file:", filepath)
        with open(filepath) as file:
            json_data = file.read()
            data = json.loads(json_data)
            try:
                cam = Camera(data["ip"], data["port"], data["user"], data["password"], "C:/Users/aggz1/MPTI Informatics/Sesestr4/cringeprak/Panocam_ONVIF_connect/venv/lib/python3.10/site-packages/wsdl")
                print("Connection successful")
                cam.see_video('rtsp://falt:panofalt1234@77.232.155.123:556')
            except:
                print("Connection error")


class App(QtWidgets.QMainWindow, main_window.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.show_dialog_window)

    def show_dialog_window(self):
        self.dialog_window = CameraDialog()
        self.dialog_window.show()


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = App()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()