import time
from socket import *

pings = 1




#Send ping 10 times 
while pings == 1:  
    
    #Create a UDP socket
    clientSocket = socket(AF_INET, SOCK_DGRAM)

    #Set a timeout value of 1 second
    clientSocket.settimeout(1)

    mes = {"type": "ConnectionRequest", "block": {"camera_conf": {"ip": "77.232.155.123", "port": "16455", "user": "falt", "password": "panofalt1234"}}}
    #Ping to server
    message = bytes(str(mes), encoding='utf-8')

    addr = ("192.168.0.103", 56000)
    
    #Send ping
    clientSocket.sendto(message, addr)

    #If data is received back from server, print 
    try:
        data, server = clientSocket.recvfrom(1024)
        end = time.time()
        print("success") 
        print(f"\n{data}")    

    #If data is not received back from server, print it has timed out  
    except timeout:
        print('REQUEST TIMED OUT')

    pings += 1