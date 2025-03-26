from socket import AF_INET, SOCK_DGRAM, socket
from json import dumps as json_dumps
from json.decoder import JSONDecodeError
from camera import Camera
from request_templates import RequestBody, implemented_types
from marshmallow import Schema
from marshmallow.exceptions import ValidationError as MarshmallowValidationError
from importlib import import_module
from structures import Speed, CameraName, Position


class UserConnectionData:
    cameras: dict[str, Camera]
    data: dict[str]   

    def __init__(self):
        self.cameras = {}
        self.data = {}

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

            #SET requests

            case "ConnectionRequest":
                # for camera_params in block["cameras"]:
                is_connected = True
                try:
                    self.cameras[CameraName(**block["camera_name"]).as_key()] = Camera(**block["camera_name"], user=block["user"], password=block["password"])
                    self.data[CameraName(**block["camera_name"]).as_key()] = {"default_values": {"speed": None}}
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
                self.data[key]["default_values"]["speed"] = Speed(**block["speed"])
                return None
            case "SetHomePosition":
                chosen_camera.setHomePosition()
                return None
            
            #GET requests

            case "GetPosition":
                cam_request = chosen_camera.getPosition()
                return {
                    "type": "Position",
                    "block": {
                        "position": Position(cam_request["PanTilt"]["x"], cam_request["PanTilt"]["y"], cam_request["Zoom"]["x"]).as_dict()
                    }
                }
            case "GetLimits":
                return {
                    "type": "Limits",
                    "block": chosen_camera.getLimits()
                }
            # case "GetRTSP":
            # case "GetAvailableCameras":
            
            #CONTROL requests

            case "ContiniousMove":
                speed = Speed(**block["speed"]) if block.get("speed", False) else None
                speed = speed or self.data[key]["default_values"]["speed"]

                if speed is None:
                    return {
                        "block": {
                            "speed": ["No default values were specified."]
                        }
                    }

                chosen_camera.continiousMove(speed, duration=block["duration"])
                return None
            case "AbsoluteMove":
                speed = Speed(**block["speed"]) if block.get("speed", False) else None
                speed = speed or self.data[key]["default_values"]["speed"]
                chosen_camera.absoluteMove(Position(**block["position"]), speed)
                return None
            case "RelativeMove":
                speed = Speed(**block["speed"]) if block.get("speed", False) else None
                speed = speed or self.data[key]["default_values"]["speed"]
                chosen_camera.relativeMove(Position(**block["relative_position"]), speed)
                return None
            case "GotoHomePosition":
                speed = Speed(**block["speed"]) if block.get("speed", False) else None
                chosen_camera.gotoHomePosition(speed)
                return None
            case "Stop":
                chosen_camera.stop(block["stop_x_y"], block["stop_zoom"])
                return None
            
            #DELETE requests

            case "CloseConnection":
                chosen_camera.stop(True, True)
                self.cameras.pop(key)
                return None
            

class Server:
    
    main_socket: socket
    connected_users: dict[str, UserConnectionData]

    # {request_type: TemplateClass()}
    __request_templates_by_name: dict[str, Schema] = {
        cls: getattr(import_module("request_templates"), cls+"Block")() for cls in implemented_types()
    }

    def __init__(self):
        self.connected_users = {}

        # getting our local address
        s = socket(AF_INET, SOCK_DGRAM)
        s.connect(("8.8.8.8", 56000))
        ip_addr = s.getsockname()[0]
        s.close()
        
        self.main_socket = socket(AF_INET, SOCK_DGRAM)
        self.main_socket.bind((ip_addr, 56000))
        print(f"[SERVER]: started at {ip_addr}")

    def run(self, client_amount=1, flush=True):
    
        while True:
            message, client = self.main_socket.recvfrom(1024)

            print(f"[{client[0]}]: ", message.decode(encoding="utf-8"), flush=flush)
            response = self.do_request(client[0], message.decode(encoding="utf-8"))

            if not response is None:
                print(f"[SERVER]: {client[0]} ", response, flush=flush)
                self.main_socket.sendto(bytes(response, encoding="utf-8"), client)

    def do_request(self, user_ip: str, request: str):
        try:
            request_dict = RequestBody().loads(request)
        except MarshmallowValidationError as err:
            return json_dumps(err.normalized_messages())
        except JSONDecodeError as err:
            return json_dumps({"Invalid syntax": f"{err.msg}, position {err.pos}"})
        
        try:
            block = self.__request_templates_by_name[request_dict["type"]].load(request_dict["block"])
        except MarshmallowValidationError as err:
            return json_dumps((err.normalized_messages()))

        if not user_ip in self.connected_users.keys():
            self.connected_users[user_ip] = UserConnectionData()

        response = self.connected_users[user_ip].do_request(request_dict["type"], block)
        if not response is None:
            response = json_dumps(response)
        
        # для каждого запроса без отдельного ответа - возвращаем сообщение о выполнении данного запроса
        else:
            response = json_dumps(
                {
                    "type": request_dict["type"] + "Response"
                }
            )
        return response
    
server = Server()
server.run()