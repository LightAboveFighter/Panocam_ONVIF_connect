from onvif import ONVIFCamera
import json

wsdl_path = 'venv/lib/python3.10/site-packages/wsdl'


with open("access_file.json", "r") as access_file:
    data = json.load(access_file)
    IP = data["cameras"][0]["ip"]
    PORT = data["cameras"][0]["port"]
    user = data["cameras"][0]["user"]
    password = data["cameras"][0]["password"]

    mycam = ONVIFCamera(IP, PORT, user, password, wsdl_path)

with open(f"Camera_main.txt", "w") as camera_info:
    
    resp = mycam.devicemgmt.GetHostname()
    camera_info.write('Camera`s hostname: ' + str(resp.Name) + '\n\n')

    # Get system date and time
    dt = mycam.devicemgmt.GetSystemDateAndTime()
    tz = dt.TimeZone
    year = dt.UTCDateTime.Date.Year
    hour = dt.UTCDateTime.Time.Hour

    camera_info.write(str(dt))
    camera_info.write("\n\n")
    camera_info.write(str(mycam.devicemgmt.GetDeviceInformation()))
    # print(mycam.)

    # media = mycam.create_media_service()
    # token = media.GetVideoEncoderConfigurations()
    # img = media.GetSnapshotUri({"ProfileToken" : token[0]._token})
    # print(img)

    # cv.imshow("", img)
    # cv.waitKey(-1)

    # mycam.get

