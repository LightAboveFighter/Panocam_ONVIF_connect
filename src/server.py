import socket
import json
from json.decoder import JSONDecodeError
from camera import Camera
import request_templates as templates
from marshmallow import Schema
from marshmallow.exceptions import ValidationError as MarshmallowValidationError
import importlib
from structures import Speed, CameraName, Position


class UserConnectionData:
    cameras: dict[str, Camera]
    data: dict[str]   

    def __init__(self):
        self.cameras = {}
        self.data = {"default_values": {}, "default_speed": {}}

    def do_request(self, request_type: str, block: dict):
        
        if "camera_name" in block.keys() and request_type != "ConnectionRequest":
            key = CameraName(**block["camera_name"]).as_key()
            chosen_camera = self.cameras.get(key, None)
            if chosen_camera is None:
                return {
                        "block": {
                            "camera_name": [ {key: "is not connected."} ]
                        }
                    }

        match request_type:
            case "ConnectionRequest":
                # for camera_params in block["cameras"]:
                is_connected = True
                try:
                    self.cameras[CameraName(**block["camera_name"]).as_key()] = Camera(**block["camera_name"], user=block["user"], password=block["password"])
                except RuntimeError:
                    is_connected = False

                return {
                    "type": "ConnectionResponse",
                    "block": {
                        "camera_name": block["camera_name"],
                        "is_connected": is_connected
                    }
                }
            case "SetMoveSpeed":
                self.data["default_values"]["default_speed"][key] = Speed(**block["speed"])
                return None
            case "ContiniousMove":
                chosen_camera.move_zoom(**block["speed"], duration=block["duration"])
                return None
            case "GetPosition":
                cam_request = chosen_camera.getPosition()
                return {
                    "type": "Position",
                    "block": {
                        "position": Position(cam_request["PanTilt"]["x"], cam_request["PanTilt"]["y"], cam_request["Zoom"]["x"]).as_dict()
                    }
                }
            # case "SetHomePosition":
            # case "MoveToHomePosition":
            case "StopMoving":
                chosen_camera.stopMoving(block["stop_x_y"], block["stop_zoom"])
                return None
            case "CloseConnection":
                chosen_camera.stopMoving(True, True)
                self.cameras.pop(key)
                return None
            # case "GetRTSP":
            # case "GetAvailableCameras":
            # case "AbsoluteMove":
            case "GetLimits":
                return {
                    "type": "Limits",
                    "block": chosen_camera.getLimits()
                }
            

class Server:

    main_socket: socket.socket
    connected_users: dict[str, UserConnectionData]

    # {request_type: TemplateClass()}
    __request_templates_by_name: dict[str, Schema] = {
        cls: getattr(importlib.import_module("request_templates"), cls+"Block")() for cls in templates.allowed_types
    }

    def __init__(self):
        self.connected_users = {}

        # getting our local address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 56000))
        ip_addr = s.getsockname()[0]
        s.close()
        
        self.main_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.main_socket.bind((ip_addr, 56000))
        print(f"[SERVER]: started at {ip_addr}")

    def run(self, client_amount=1, flush=True):
    
        while True:
            message, client = self.main_socket.recvfrom(1024)

            print(f"[{client[0]}]: ", message.decode(encoding="utf-8"), flush=flush)
            response = self.do_request(client[0], message.decode(encoding="utf-8"))

            if not response is None:
                print(f"[SERVER]: {client[0]} ", response, flush=True)
                self.main_socket.sendto(bytes(response, encoding="utf-8"), client)

    def do_request(self, user_ip: str, request: str):
        try:
            request_dict = templates.RequestBody().loads(request)
        except MarshmallowValidationError as err:
            return json.dumps(err.normalized_messages())
        except JSONDecodeError as err:
            return json.dumps({"Invalid syntax": f"{err.msg}, position {err.pos}"})
        
        try:
            block = self.__request_templates_by_name[request_dict["type"]].load(request_dict["block"])
        except MarshmallowValidationError as err:
            return json.dumps((err.normalized_messages()))

        if not user_ip in self.connected_users.keys():
            self.connected_users[user_ip] = UserConnectionData()

        response = self.connected_users[user_ip].do_request(request_dict["type"], block)
        if not response is None:
            response = json.dumps(response)
        
        # для каждого запроса без отдельного ответа - возвращаем сообщение о выполнении данного запроса
        else:
            response = json.dumps(
                {
                    "type": request_dict["type"] + "Response"
                }
            )
        return response
    
server = Server()
server.run()