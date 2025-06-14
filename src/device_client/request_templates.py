from marshmallow import Schema, fields, validates, post_load
from marshmallow.exceptions import ValidationError as MarshmallowValidationError
from marshmallow.validate import Range
from inspect import getmembers, isclass
from sys import modules


def implemented_types():
    return [
        cls.__name__.replace("Block", "")
        for _, cls in getmembers(modules[__name__], isclass)
        if (cls.__module__ == __name__) and (cls.__name__.count("Block") != 0)
    ]


# GENERAL templates


class RequestBody(Schema):
    type = fields.String(required=True)
    block = fields.Dict(required=False)

    def __init__(self, *args, **kwargs):
        self.allowed_types = implemented_types()
        super().__init__(*args, **kwargs)

    @validates("type")
    def check_type(self, type, **kwargs):
        if not type in self.allowed_types:
            raise MarshmallowValidationError(message="Unknown type.", field_name="type")


# STRUCTURES templates


class CameraNameTemplate(Schema):
    ip = fields.IP(required=True)
    port = fields.Integer(required=True, strict=False, validate=Range(0, 65536))

    @post_load
    def set_ip_as_str(self, data, *args, **kwargs):
        data["ip"] = str(data["ip"])
        return data


class PositionTemplate(Schema):
    x = fields.Float(required=True)
    y = fields.Float(required=True)
    zoom = fields.Float(required=True)


class SpeedTemplate(Schema):
    x_speed = fields.Float()
    y_speed = fields.Float()
    zoom_speed = fields.Float()

    def __init__(self, x_default=0, y_default=0, zoom_default=0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["x_speed"].load_default = float(x_default)
        self.fields["y_speed"].load_default = float(y_default)
        self.fields["zoom_speed"].load_default = float(zoom_default)

    def loads(self, *args, **kwargs):
        loads_result = super().loads(*args, **kwargs)
        print(
            abs(loads_result["x_speed"])
            + abs(loads_result["y_speed"])
            + abs(loads_result["zoom_speed"])
        )
        if (
            abs(loads_result["x_speed"])
            + abs(loads_result["y_speed"])
            + abs(loads_result["zoom_speed"])
            == 0
        ):
            raise MarshmallowValidationError(
                message="Length of speed vector must be greater than 0.",
                field_name="(x_speed, y_speed, zoom_speed)",
            )
        return loads_result


# BLOCK templates

# GENERAL BLOCK templates


class NeedsCameraSchema(Schema):
    camera_name = fields.Nested(CameraNameTemplate, many=False, required=True)


# SET BLOCK requests templates


class ConnectionRequestBlock(NeedsCameraSchema):
    user = fields.String(required=True)
    password = fields.String(required=True)


class SetMoveSpeedBlock(NeedsCameraSchema):
    speed = fields.Nested(SpeedTemplate, many=False, required=True)


class SetHomePositionBlock(NeedsCameraSchema):
    pass


# GET BLOCK requests templates


class GetLocalCamerasBlock(Schema):
    scan_timeout = fields.Integer(required=False, strict=False, validate=Range(0, 100))


class GetRemoteCameraBlock(Schema):
    scan_timeout = fields.Integer(required=True, strict=False, validate=Range(0, 100))
    ip = fields.IP(required=True)


class GetPositionBlock(NeedsCameraSchema):
    pass


class GetLimitsBlock(NeedsCameraSchema):
    pass


class GetRTSPBlock(NeedsCameraSchema):
    pass

# CONTROL BLOCK requests templates


class ContiniousMoveBlock(NeedsCameraSchema):
    duration = fields.Float(required=True, validate=Range(min=0))
    speed = fields.Nested(SpeedTemplate, many=False, required=False, load_default=None)


class AbsoluteMoveBlock(NeedsCameraSchema):
    position = fields.Nested(PositionTemplate, many=False, required=True)
    speed = fields.Nested(SpeedTemplate, many=False, required=False, load_default=None)


class RelativeMoveBlock(NeedsCameraSchema):
    relative_position = fields.Nested(PositionTemplate, many=False, required=True)
    speed = fields.Nested(SpeedTemplate, many=False, required=False, load_default=None)


class GotoHomePositionBlock(NeedsCameraSchema):
    speed = fields.Nested(SpeedTemplate, many=False, required=False, load_default=None)


class StopBlock(NeedsCameraSchema):
    stop_x_y = fields.Bool()
    stop_zoom = fields.Bool()


# DELETE BLOCK requests templates


class CloseConnectionBlock(NeedsCameraSchema):
    pass
