from socket import (
    socket,
    AF_INET,
    SOCK_DGRAM,
    timeout,
    SOL_SOCKET,
    SO_REUSEADDR,
    IPPROTO_IP,
    IP_MULTICAST_TTL,
)
from uuid import uuid4
import xml.etree.ElementTree as ET
from threading import Thread, Event

probe_xml = """<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope 
    xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
    xmlns:wsa="http://www.w3.org/2005/08/addressing"
    xmlns:wsd="http://schemas.xmlsoap.org/ws/2005/04/discovery"
    xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
    <soap:Header>
        <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
        <wsa:MessageID>uuid:unique-id</wsa:MessageID>
        <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
    </soap:Header>
    <soap:Body>
        <wsd:Probe>
            <wsd:Types>tds:Device</wsd:Types>
        </wsd:Probe>
    </soap:Body>
</soap:Envelope>"""


def scan_remote_address(target_ip, scan_timeout=2):
    """
    :param target_ip: IP, which will be checked for ONVIF Camera existance. Must have str conversion
    :return: (data, addr) if exist, else None"""

    sock = socket(AF_INET, SOCK_DGRAM)
    sock.settimeout(scan_timeout)
    sock.sendto(probe_xml.encode(), (str(target_ip), 3702))

    try:
        data, addr = sock.recvfrom(4096)
        return (data, addr)
    except timeout:
        return None


def scan_local_subnet(scan_timeout=2):
    """
    Сканирует все устройства в подсети через multicast.
    Автоматически определяет локальный IP.

    :param timeout: Timeout of waiting for answer (seconds)
    :return: List of found cameras in dict: {ip, xaddr, types}
    """

    # Остальной код остается без изменений
    message_id = f"uuid:{uuid4()}"
    probe_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <soap:Envelope
        xmlns:soap="http://www.w3.org/2003/05/soap-envelope"
        xmlns:wsa="http://www.w3.org/2005/08/addressing"
        xmlns:wsd="http://schemas.xmlsoap.org/ws/2005/04/discovery"
        xmlns:tds="http://www.onvif.org/ver10/device/wsdl">
        <soap:Header>
            <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>
            <wsa:MessageID>{message_id}</wsa:MessageID>
            <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>
        </soap:Header>
        <soap:Body>
            <wsd:Probe>
                <wsd:Types>tds:Device</wsd:Types>
            </wsd:Probe>
        </soap:Body>
    </soap:Envelope>"""

    mcast_group = "239.255.255.250"
    mcast_port = 3702

    sock = socket(AF_INET, SOCK_DGRAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, 2)
    sock.settimeout(scan_timeout)

    sock.sendto(probe_xml.encode(), (mcast_group, mcast_port))

    devices = []
    stop_event = Event()

    def listen():
        while not stop_event.is_set():
            try:
                data, addr = sock.recvfrom(4096)
                root = ET.fromstring(data.decode())
                ns = {
                    "wsd": "http://schemas.xmlsoap.org/ws/2005/04/discovery",
                    "wsa": "http://www.w3.org/2005/08/addressing",
                }
                xaddrs = root.find(".//wsd:XAddrs", ns).text.split()[0]
                devices.append(
                    {
                        "ip": addr[0],
                        "xaddr": xaddrs,
                        "types": root.find(".//wsd:Types", ns).text,
                    }
                )
            except (timeout, ET.ParseError, AttributeError):
                pass

    listener = Thread(target=listen)
    listener.start()
    stop_event.wait(scan_timeout + 1)
    stop_event.set()
    listener.join()
    sock.close()

    return devices
