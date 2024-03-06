import socket
import time
from .segment import Segment

class Connection:
    def __init__(self, ip : str, port : int):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((ip, port))
        print(f"[!] Server started on {ip}:{port}")
        self.ip = ip
        self.port = port


    """
    Connect to dest
    """
    def connect(self, dest):
        self.server_socket.connect(dest)


    """
    Send data msg to dest
    """
    def send_data(self, msg, dest):
        # print(f"[!] Sending message to {dest[0]}:{dest[1]}")
        self.server_socket.sendto(msg, dest)


    """
    Listen single UDP datagram within timeout and convert into segment
    """
    def listen_single_segment(self) -> Segment:
        request = self.server_socket.recvfrom(32768)
        return request


    """
    Setting timeout
    """
    def set_timeout(self, timeout=20):
        try:
            self.server_socket.settimeout(timeout)
        except TimeoutError:
            raise Exception('Server Timeout')


    """
    Release UDP socket
    """
    def close_socket(self):
        self.server_socket.close()
