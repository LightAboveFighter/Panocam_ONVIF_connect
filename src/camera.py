from onvif import ONVIFCamera, ONVIFService
from onvif.exceptions import ONVIFError
from cv2 import VideoCapture, imshow, waitKey
from json import load as json_load
from time import sleep
from zeep.transports import Transport
from os.path import dirname, join
from inspect import getfile
from re import sub as re_sub
from structures import Position


class Camera:
    cam: ONVIFCamera
    media_service: ONVIFService | None
    ptz_service: ONVIFService | None

    def __init__(self, ip: str, port: int, user: str, password: str, config_path = None, timeout: int = 1):
        """
        config_path - if you want initialization from config file
        """
        if not config_path is None:
            self.__init_from_config(config_path, timeout)
            return self
        self.ip = str(ip)
        self.port = port
        self.user = user
        self.password = password
        self.media_service = None
        self.ptz_service = None
        self.profile_token = None

        self.__set_connection(timeout)

    def __init_from_config(self, config_path: str, timeout: int):
        with open(config_path, "r") as access_file:
            data = json_load(access_file)
            self.ip = data["ip"]
            self.port = data["port"]
            self.user = data["user"]
            self.password = data["password"]
        self.__set_connection(timeout)

    
    def __set_connection(self, timeout: int):
        
        wsdl_path = join(dirname(dirname(getfile(ONVIFCamera))), "wsdl")
        self.cam = ONVIFCamera(self.ip, self.port, self.user, self.password, wsdl_path, transport=Transport(timeout=timeout))

        capabilities = self.getCapabilities()
        if capabilities["Device"]["XAddr"].find("192.168.") != -1:
            self.cam.xaddrs = { 
                url: re_sub(r'192\.168\.\d*\.\d*', self.ip+":"+str(self.port), addr) 
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
                self.profile_token = self.getProfileToken()
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
        request = self.ptz_service.create_type("GetStatus")
        request.ProfileToken = self.profile_token
        return self.ptz_service.GetStatus(request)
    
    def getPosition(self):
        return self.getPtzStatus().Position
    
    @__profile_token
    @__ptz_service
    def continiousMove(self, speed: Speed, duration = 0.5, method_is_blocking = True):
        request = self.ptz_service.create_type("ContinuousMove")
        request.ProfileToken = self.profile_token

        request.Velocity = speed.as_onvif_dict()

        self.ptz_service.ContinuousMove(request)
        
        if method_is_blocking:
            sleep(duration)
            self.stop(True, True)
        else:   
            pass

    @__profile_token
    @__ptz_service
    def absoluteMove(self, position: Position, speed: Speed = None):
        request = self.ptz_service.create_type("AbsoluteMove")
        request.ProfileToken = self.profile_token
        request.Position = position.as_onvif_dict()  

        if not speed is None:
            request.Speed = speed.as_onvif_dict()

        return self.ptz_service.AbsoluteMove(request)
    
    @__profile_token
    @__ptz_service
    def stop(self, stop_x_y: bool, stop_zoom: bool):
        request = self.ptz_service.create_type("Stop")
        request.ProfileToken = self.profile_token
        request.PanTilt = stop_x_y
        request.Zoom = stop_zoom

        return self.ptz_service.Stop(request)
    
    @__ptz_service
    def getPTZConfiguration(self):
        return self.getProfiles()[0].PTZConfiguration
    
    def getLimits(self):
        ptz_config = self.getPTZConfiguration()
        tilt_ranges = ptz_config["PanTiltLimits"]["Range"]
        return {
            "position_min": Position(tilt_ranges["XRange"]["Min"], tilt_ranges["XRange"]["Min"], ptz_config["ZoomLimits"]["Range"]["XRange"]["Min"]).as_dict(),
            "position_max": Position(tilt_ranges["XRange"]["Max"], tilt_ranges["XRange"]["Max"], ptz_config["ZoomLimits"]["Range"]["XRange"]["Max"]).as_dict()
        }
    
    @__profile_token
    @__ptz_service
    def gotoHomePosition(self):
        request = self.ptz_service.create_type("GotoHomePosition")
        request.ProfileToken = self.profile_token
        return self.ptz_service.GotoHomePosition(request)
    
    @__profile_token
    @__ptz_service
    def setHomePosition(self):
        """set active position as home"""
        request = self.ptz_service.create_type("SetHomePosition")
        request.ProfileToken = self.profile_token
        return self.ptz_service.SetHomePosition(request)

    def see_video(self, video_stream_link: str):

        vcap = VideoCapture(video_stream_link)
        while(1):
            success, frame = vcap.read()
            imshow('Camera_{self.ip}', frame)
            waitKey(1)

    def reboot(self):
        return self.cam.devicemgmt.SystemReboot()