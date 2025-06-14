from dataclasses import dataclass, asdict

@dataclass
class CameraName:
    ip: str
    port: int

    def as_key(self):
        return f"{self.ip}:self.port"
    
    def as_dict(self):
        return asdict(self)


@dataclass
class Position:
    x: float
    y: float
    zoom: float

    def as_dict(self):
        return asdict(self)
    
    def as_onvif_dict(self):
        return {'PanTilt': {"x": self.x, "y": self.y}, 'Zoom': self.zoom}


@dataclass
class Speed:
    x_speed: float
    y_speed: float
    zoom_speed: float

    def __post_init__(self):
        if abs(self.x_speed) + abs(self.y_speed) + abs(self.zoom_speed) == 0:
            raise TypeError("Non-positive or zero Speed vector's lenght.")
        
    def as_dict(self):
        return asdict(self)
    
    def as_onvif_dict(self):
        return {'PanTilt': {"x": self.x_speed, "y": self.y_speed}, 'Zoom': self.zoom_speed}
