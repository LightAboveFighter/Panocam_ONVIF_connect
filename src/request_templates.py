from marshmallow import Schema, fields, validates, post_load
from marshmallow.exceptions import ValidationError as MarshmallowValidationError
from marshmallow.validate import Range
from inspect import getmembers, isclass
from sys import modules


def implemented_types():
    return [cls.__name__.replace("Block", "") for _, cls in getmembers(modules[__name__], isclass) if (cls.__module__ == __name__) and (cls.__name__.count("Block") != 0)] 


class RequestBody(Schema):
    type = fields.String(required=True)
    block = fields.Dict(required=False)
        
    def __init__(self, *args, **kwargs):
        self.allowed_types = implemented_types()
        super().__init__(*args, **kwargs)

    @validates("type")
    def check_type(self, type):
        if not type in self.allowed_types:
            raise MarshmallowValidationError(message="Unknown type.", field_name="type")
        

class CameraNameTemplate(Schema):
    ip = fields.IP(required=True)
    port = fields.Integer(required=True, allow_string=True, strict=False, validate=Range(0, 65536))

    @post_load
    def set_ip_as_str(self, data, *args, **kwargs):
        data["ip"] = str(data["ip"])
        return data


class NeedsCameraSchema(Schema):
    camera_name = fields.Nested(CameraNameTemplate, many=False, required=True)


class PositionTemplate(Schema):
    x = fields.Float(required=True)
    y = fields.Float(required=True)
    zoom = fields.Float(required=True)
    
    def __init__(self, x_default = 0, y_default = 0, zoom_default = 0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["x"].load_default = float(x_default)
        self.fields["y"].load_default = float(y_default)
        self.fields["zoom"].load_default = float(zoom_default)


class SpeedTemplate(Schema):
    x_speed = fields.Float()
    y_speed = fields.Float()
    zoom_speed = fields.Float()

    def __init__(self, x_default = 0, y_default = 0, zoom_default = 0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["x_speed"].load_default = float(x_default)
        self.fields["y_speed"].load_default = float(y_default)
        self.fields["zoom_speed"].load_default = float(zoom_default)
    
    def loads(self, *args, **kwargs):
        loads_result = super().loads(*args, **kwargs)
        print(abs(loads_result["x_speed"]) + abs(loads_result["y_speed"]) + abs(loads_result["zoom_speed"]))
        if abs(loads_result["x_speed"]) + abs(loads_result["y_speed"]) + abs(loads_result["zoom_speed"]) == 0:
            raise MarshmallowValidationError(message="Length of speed vector must be greater than 0.", field_name="(x_speed, y_speed, zoom_speed)")
        return loads_result


class ConnectionRequestBlock(NeedsCameraSchema):
    user = fields.String(required=True)
    password = fields.String(required=True)


class SetMoveSpeedBlock(NeedsCameraSchema):
    speed = fields.Nested(SpeedTemplate, many=False, required=True)


class ContiniousMoveBlock(NeedsCameraSchema):
    duration = fields.Float(required=True, validate=Range(min=0))
    speed = fields.Nested(SpeedTemplate, many=False, required=True)

    # def __init__(self, x_default = 0, y_default = 0, zoom_default = 0, *args, **kwargs):
    #     self.default_speed = (x_default, y_default, zoom_default)
    #     super().__init__(*args, **kwargs)
        # self.fields["speed"].fields["x"] = float(x_default)
        # self.fields["speed"].fields["y"] = float(y_default)
        # self.fields["speed"].fields["zoom"] = float(zoom_default)
        # self.fields["speed"] = SpeedTemplate(x_default, y_default, zoom_default)
        # print(self) #["x"].load_default = x_default
        # ["x"].load_default = x_default

    # @post_load
    # def set_defaults(self, data, **kwargs):
    #     data["speed"] = SpeedTemplate(self.default_speed[0], self.default_speed[1], self.default_speed[2]).load(data["speed"])
    #     print(data["speed"], self.default_speed)
    #     return data


class GetPositionBlock(NeedsCameraSchema):
    pass


class SetHomePositionBlock(NeedsCameraSchema):
    pass


class GotoHomePositionBlock(NeedsCameraSchema):
    speed = fields.Nested(SpeedTemplate, many=False, required=False, load_default=None)
    

class CloseConnectionBlock(NeedsCameraSchema):
    pass

# class GetRTSPBlock(Schema):

# class GetAvailableCamerasBlock(Schema):

class StopBlock(NeedsCameraSchema):
    stop_x_y = fields.Bool()
    stop_zoom = fields.Bool()


class AbsoluteMoveBlock(NeedsCameraSchema):
    position = fields.Nested(PositionTemplate, many=False, required=True)
    speed = fields.Nested(SpeedTemplate, many=False, required=False, load_default=None)


class GetLimitsBlock(NeedsCameraSchema):
    pass