from onvif import ONVIFCamera, exceptions, ONVIFService
import cv2
import json
import time
import glob
import os
import re

class Camera:
    cam: ONVIFCamera
    media_service: ONVIFService | None
    ptz_service: ONVIFService | None

    def __init__(self, ip: str, port: int, user: str, password: str, wsdl_path = None, config_path = None):
        """
        wsdl_path - only if you have specified path to wsdl in onvif library
        config_path - if you want initialization from config file
        """
        if not config_path is None:
            self.__init_from_config(config_path)
            return self
        self.ip = str(ip)
        self.port = port
        self.user = user
        self.password = password
        self.media_service = None
        self.ptz_service = None
        self.profile_token = None

        self.__set_connection(wsdl_path)

    def __init_from_config(self, config_path: str, wsdl_path: str):
        with open(config_path, "r") as access_file:
            data = json.load(access_file)
            self.ip = data["ip"]
            self.port = data["port"]
            self.user = data["user"]
            self.password = data["password"]
        self.__set_connection(wsdl_path)

    
    def __set_connection(self, wsdl_path: str):
        if not wsdl_path is None:
            self.cam = ONVIFCamera(self.ip, self.port, self.user, self.password, wsdl_path)
            return
        try:
            self.cam = ONVIFCamera(self.ip, self.port, self.user, self.password, "/etc/onvif/wsdl/")
        except exceptions.ONVIFError:
            self.cam = ONVIFCamera(self.ip, self.port, self.user, self.password, os.path.join(glob.glob("venv/lib/python*")[0], "site-packages/wsdl") ) 

        capabilities = self.getCapabilities()
        if capabilities["Device"]["XAddr"].find("192.168.") != -1:
            self.cam.xaddrs = { 
                url: re.sub(r'192\.168\.\d*\.\d*', self.ip+":"+str(self.port), addr) 
                for url, addr in self.cam.xaddrs.items() 
                }

    def __media_service(func):
        def _wrapper(*args, **kwargs):
            self = args[0] if len(args) > 0 else kwargs["self"]
            assert isinstance(self, Camera)
            if self.media_service is None:
                self.media_service = self.cam.create_media_service()
                if self.media_service is None:
                    raise RuntimeError("Can't create media service due to connection")
            return func(*args, **kwargs)
        return _wrapper
    

    def __ptz_service(func):
        def _wrapper(*args, **kwargs):
            self = args[0] if len(args) > 0 else kwargs["self"]
            assert isinstance(self, Camera)
            if self.ptz_service is None:
                self.ptz_service = self.cam.create_ptz_service()
                if self.ptz_service is None:
                    raise RuntimeError("Can't create ptz service due to connection")
            return func(*args, **kwargs)
        return _wrapper

    def __profile_token(func):
        def _wrapper(*args, **kwargs):
            self = args[0] if len(args) > 0 else kwargs["self"]
            assert isinstance(self, Camera)
            if self.profile_token is None:
                self.profile_token = self.getProfiles()[0].token
            return func(*args, **kwargs)
        return _wrapper

    def getDeviceInformation(self):
        return self.cam.devicemgmt.GetDeviceInformation()
    
    def getHostname(self):
        return self.cam.devicemgmt.GetHostname()

    def getCapabilities(self):
        return self.cam.devicemgmt.GetCapabilities()
    
    def getServices(self):
        return self.cam.devicemgmt.GetServices({"IncludeCapability": True})
    
    @__media_service
    def getProfiles(self):
        # if self.media_service is None:
        #     self.media_service = self.cam.create_media_service()
        profiles = self.media_service.GetProfiles()
        if profiles is None:
            raise RuntimeError("Can't get profiles due to connection")
        return profiles
    
    @__ptz_service
    def getPtzCapabilities(self):
        return self.ptz_service.GetServiceCapabilities()
    
    def getProfileToken(self):
        return self.getProfiles()[0].token
    
    @__profile_token
    @__ptz_service
    def getPtzStatus(self):
        return self.ptz_service.GetStatus({'ProfileToken': self.profile_token})
    
    def getPosition(self):
        return self.getPtzStatus().Position
    
    @__profile_token
    @__ptz_service
    def move_zoom(self, x_speed = 0, y_speed = 0, zoom_speed = 0, duration = 0.5, method_is_blocking = True):
        if (abs(x_speed) + abs(y_speed) + abs(zoom_speed)) == 0:
            return

        self.ptz_service.ContinuousMove(
            {'ProfileToken': self.profile_token, 'Velocity': {'PanTilt': {"x": x_speed, "y": y_speed}, 'Zoom': zoom_speed}}
        )
        
        if method_is_blocking:
            time.sleep(duration)
            self.ptz_service.Stop({'ProfileToken': self.profile_token, 'PanTilt': True, 'Zoom': True})
        else:   
            pass
    
    @__ptz_service
    def getPTZConfiguration(self):
        return self.getProfiles()[0].PTZConfiguration
    
    def getLimits(self):
        """return [ (x_min, x_max), (y_min, y_max), (zoom_min, zoom_max) ]"""
        ptz_config = self.getPTZConfiguration()
        tilt_ranges = ptz_config["PanTiltLimits"]["Range"]
        x_range = ( tilt_ranges["XRange"]["Min"], tilt_ranges["XRange"]["Max"] )
        y_range = ( tilt_ranges["YRange"]["Min"], tilt_ranges["YRange"]["Max"] )
        zoom_range = ( ptz_config["ZoomLimits"]["Range"]["XRange"]["Min"], ptz_config["ZoomLimits"]["Range"]["XRange"]["Max"] )
        return [x_range, y_range, zoom_range]
    
    # @__ptz_service
    # def gotoHomePosition(self):
    #     return self.ptz_service.GotoHomePosition({'ProfileToken': self.profile_token})
    
    # @__ptz_service
    # def setHomePosition(self):
    #     """set active position as home"""
    #     self.ptz_service.SetHomePosition({'ProfileToken': self.profile_token})

    def see_video(self, video_stream_link: str):

        vcap = cv2.VideoCapture(video_stream_link)
        while(1):
            success, frame = vcap.read()
            cv2.imshow('Camera_{self.ip}', frame)
            cv2.waitKey(1)

    def reboot(self):
        return self.cam.devicemgmt.SystemReboot()