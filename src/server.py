import socket
from dataclasses import dataclass, asdict
import json
from camera import Camera

class MissedRequiredField(Exception):
    pass

class UserConnectionData:
    cameras: dict[str, Camera]


@dataclass
class CameraConf:
    ip: str
    port: int

@dataclass
class Position:
    x: float
    y: float
    zoom: float

Messages_descriptions = {
    "ConnectionRequest": {
        "required_fields": ["ip", "port", "user", "password"],
        "response": {
            "type": "ConnectionResponse"
        }
    },
    "SetMoveVelocity": {
        "required_fields": ["x_velocity", "y_velocity", "zoom_velocity"],
        "response": None
    },
    "ContiniousMove": {
        "required_fields": ["duration"],
        "response": None
    },
    "GetPosition": {
        "required_fields": [],
        "response": {
            "type": "Position",
            "block": {
                "position": Position
            }
        }
    },
    "SetHomePosition": {
        "required_fields": ["position"],
        "response": {
            "type": "ConnectionResponse"
        }
    },
    "MoveToHomePosition": {
        "required_fields": [],
        "response": {
            "type": "ConnectionResponse"
        }
    },
    "CloseConnection": {
        "required_fields": [],
        "response": {
            "type": "ConnectionResponse"
        }
    },
    "GetRTSP": {
        "required_fields": [],
        "response": {
            "type": "ConnectionResponse"
        }
    },
    "GetAvailableCameras": {
        "required_fields": [],
        "response": {
            "type": "ConnectionResponse"
        }
    },
    "StopMoving": {
        "required_fields": [],
        "response": {
            "type": "ConnectionResponse"
        }
    },
    "AbsoluteMove": {
        "required_fields": ["position", "velocity"],
        "response": {
            "type": "ConnectionResponse"
        }
    },
    "GetLimits": { # отсылаем лимиты при подключении к камере. Узнать чему соответствуют макс и мин значения зума (х2 или х30)
        "required_fields": [],
        "response": {
            "type": "ConnectionResponse"
        }
    },
}

with open("example.json", "w") as file:
    json.dump(asdict(Position(1, 2, 3)), file)

print(asdict(Position(2,5,6)))

# def check_required_fields()

def do_request(client_cell, request: dict) -> tuple[int, dict]:

    request_type = request["type"]
    print(request)

    # match request_type:
    #     case "ConnectionRequest":

    #         client_cell = {
    #             "cameras": []
    #         }
    #         client_cell["cameras"].append( Camera() )
    #         return 0
    #     case "SetMoveVelocity":
    #     case "ContiniousMove":
    #     case "GetPosition":
    #     case "SetHomePosition":
    #     case "MoveToHomePosition":
    #     case "CloseConnection":
    #     case "GetRTSP":
    #     case "GetAvailableCameras":
    #     case "StopMoving":
    #     case "AbsoluteMove":
    #         pass
    #     case "GetLimits":
    #         pass

def run_server():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('192.168.0.221', 56000))
    # server_socket.listen(1)

    clients = {}

    while True:

        message, client_address = server_socket.recvfrom(1028)
        clients[client_address] = None

        res, response = do_request(clients[client_address], dict(message))

        if res < 0:
            print(f"[{client_address}]: IncorrectValue")
            server_socket.send({"type": "IncorrectValue"})
            break
        print(f"[{client_address}]: {dict(message)['type']}")
        if res == 0:
            continue
        
        server_socket.send(response)
        print(f"[SERVER]: {response['type']} to [{client_address}]")

        # client_socket, client_address = server_socket.accept()
        # print(f"[{client_address}]: Connection accepted")

        while True:
            message, client_address = server_socket.recvfrom(1028)
            res, response = do_request(dict(message))

            if res < 0:
                print(f"[{client_address}]: IncorrectValue")
                server_socket.send({"type": "IncorrectValue"})
                break
            print(f"[{client_address}]: {dict(message)['type']}")
            if res == 0:
                continue
            
            server_socket.send(response)
            print(f"[SERVER]: {response['type']} to [{client_address}]")

        
        # client_socket.close()
        print(f"[SERVER]: Connection closed: [{client_address}]")




# import asyncio
# import random

# class EchoServerProtocol:
#     def connection_made(self, transport):
#         self.transport = transport

#     def datagram_received(self, data, addr):
#         message = data.decode()
#         print('Received %r from %s' % (message, addr))
#         rand = random.randint(0, 10)
#         if rand >= 4:
#             print('Send %r to %s' % (message, addr))
#             self.transport.sendto(data, addr)
#         else:
#             print('Send %r to %s' % (message, addr))
#             self.transport.sendto(data, addr)

# run_server()