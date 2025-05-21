import sys
import os

current_file_path = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file_path)
project_src_path = os.path.abspath(os.path.join(current_dir, "..", "src"))
sys.path.insert(0, project_src_path)

from camera import Camera

# try:
#     cam = Camera("77.232.155.123", 16455, "falt", "panofalt1234", "C:/Users/aggz1/MPTI Informatics/Sesestr4/cringeprak/Panocam_ONVIF_connect/venv/lib/python3.10/site-packages/wsdl")
#     print("Connection successful")
#     cam.see_video('rtsp://falt:panofalt1234@77.232.155.123:556')
#     # cam.get_video_stream('rtsp://falt:panofalt1234@77.232.155.123:556')
# except:
#     print("Connection error")

cam = Camera("77.232.155.123", 16068, "falt", "panofalt1234")
cam.see_video("rtsp://falt:panofalt1234@77.232.155.123:559")
