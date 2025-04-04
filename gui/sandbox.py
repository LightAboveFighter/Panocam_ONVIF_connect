import sys
sys.path.insert(1, 'C:/Users/aggz1/MPTI Informatics/Sesestr4/cringeprak/Panocam_ONVIF_connect/src')
from camera import Camera

# try:
#     cam = Camera("77.232.155.123", 16455, "falt", "panofalt1234", "C:/Users/aggz1/MPTI Informatics/Sesestr4/cringeprak/Panocam_ONVIF_connect/venv/lib/python3.10/site-packages/wsdl")
#     print("Connection successful")
#     cam.see_video('rtsp://falt:panofalt1234@77.232.155.123:556')
#     # cam.get_video_stream('rtsp://falt:panofalt1234@77.232.155.123:556')
# except:
#     print("Connection error")

cam = Camera("77.232.155.123", 16068, "falt", "panofalt1234")
cam.see_video('rtsp://falt:panofalt1234@77.232.155.123:559')
