from lib.connection import Connection
from lib.segment import Segment
import sys
import random
import socket

SYN_FLAG = 0b0010
ACK_FLAG = 0b1000
FIN_FLAG = 0b0001

class Client:
    def __init__(self, port, file_path):
        self.client = Connection('127.0.0.1', port)
        self.file_path = file_path
        self.server_addr = 0


    def listen_file_transfer(self, server_addr):

        """
        Starting handshake if hasnt been established
        """
        established = False
        if self.server_addr == 0:
            print(f"[!] [File Transfer] Three way handshake hasn't been established")
            print(f"[!] [Handshake] Starting handshake to {server_addr[0]}:{server_addr[1]}")
            print(f"[!] [Handshake] Sending request for handshake to server")
            self.client.send_data(Segment(flag=(FIN_FLAG | ACK_FLAG)).get_bytes(), server_addr)
            established = self.three_way_handshake(server_addr)
        else:
            established = True

        while not established:
            retry = input(f'[?] [Handshake] Failed, want to retry handshake? (y/n): ')
            if retry == 'n': break
            print(f"[!] [Handshake] Sending request for handshake to server")
            self.client.send_data(Segment().get_bytes(), server_addr)
            established = self.three_way_handshake(server_addr)

        if not established:
            print(f"[!] [File Transfer] File transfer failed")
            exit()


        """
        Listening to file transfer
        """
        print(f'[!] [File Transfer] Waiting for file transfer')
        self.receive_file()
        self.client.close_socket()


    def receive_file(self):
        req_num = 0
        self.client.set_timeout(20)
        try:
            with open(self.file_path, "wb") as file:
                while True:
                    res = self.client.listen_single_segment()[0]
                    segment = Segment().set_from_bytes(res)
                    seg_header = segment.get_header()
                    seq_num = seg_header['seq_number']
                    print(f"[!] [File Transfer] [Segment SEQ={req_num}] Received")

                    if seg_header['flag'] == FIN_FLAG:
                        print(f"[!] [File Transfer] FIN segment received")
                        self.client.send_data(Segment(
                            ack_number=req_num,
                            flag=FIN_FLAG).get_bytes(),
                            self.server_addr)
                        break

                    # Validate checksum
                    if segment.valid_checksum() and seq_num == req_num:
                        file.write(segment.get_payload())
                        self.client.send_data(Segment(
                            ack_number=req_num,
                            flag=ACK_FLAG).get_bytes(),
                            self.server_addr)
                        print(f"[!] [File Transfer] [Segment SEQ={req_num}] ACK sent")
                        req_num += 1

                    else:
                        print(f'[!] [File Transfer] [Segment SEQ={req_num}] Error. Sending request for this segment')
                        self.client.send_data(Segment(
                            ack_number=req_num,
                            flag=ACK_FLAG).get_bytes(),
                            self.server_addr)

        except socket.timeout:
            print(f"[!] [File Transfer] Server Timeout")
            exit()


        print(f"[!] File successfully received and saved on {self.file_path}")


    def three_way_handshake(self, server_addr) -> bool:
        print(f"[!] [Handshake] Client handshake started")

        self.client.set_timeout(10)
        while True:
            try:
                # Waiting for segment from server
                print(f"[!] [Handshake] Waiting for Segment from server")
                segment, server_add = self.client.listen_single_segment()
                seg_header = Segment().set_from_bytes(segment).get_header()

                # Validate address
                if server_add != server_addr:
                    raise ValueError(f"Wrong server connection. Expected {server_addr[0]}:{server_addr[1]}, got {server_add[0]}:{server_add[1]}")


                # If SYN Flag received then send SYN_ACK
                if seg_header['flag'] == SYN_FLAG:
                    print(f"[!] [Handshake] SYN Segment received")

                    # Sending SYN_ACK segment to server
                    seq_number = 0
                    syn_ack_segment = Segment(
                                        seq_number=seq_number,
                                        ack_number=seg_header['seq_number']+1,
                                        flag=(SYN_FLAG | ACK_FLAG))
                    print(f"[!] [Handshake] Sending SYN_ACK to {server_addr[0]}:{server_addr[1]}")
                    self.client.send_data(syn_ack_segment.get_bytes(), server_addr)
                    print(f'[!] [Handshake] SYN_ACK Segment delivered')


                # If ACK Flag received then connection established
                elif seg_header['flag'] == ACK_FLAG:
                    print(f"[!] [Handshake] ACK Segment received")
                    break


                # If flag is not SYN or ACK then send SYN_ACK again to server
                else:
                    print(f"[!] [Handshake] Segment received is not SYN or ACK, retry SYN_ACK")

                    # Sending SYN_ACK segment to server
                    seq_number = random.randint(1000, 9999)
                    syn_ack_segment = Segment(
                                        seq_number=seq_number,
                                        ack_number=seg_header['seq_number']+1,
                                        flag=(SYN_FLAG | ACK_FLAG))
                    print(f"[!] [Handshake] Sending SYN_ACK to {server_addr[0]}:{server_addr[1]}")
                    self.client.send_data(syn_ack_segment.get_bytes(), server_addr)
                    print(f'[!] [Handshake] SYN_ACK Segment delivered')

            except TimeoutError:
                print(f'[!] [Handshake] Server timeout')
                print(f'[!] [Handshake] Connection failed')
                print(f'[!] [Handshake] Retry Handshake')
                self.listen_file_transfer(server_addr)

            except Exception as e:
                print(f'[!] [Handshake] {e.args[0]}')
                print(f'[!] [Handshake] Connection failed')
                return False

        # Connection established
        print(f"[!] [Handshake] Connection established to {server_addr[0]}:{server_addr[1]}")
        self.server_addr = server_addr
        return True


if __name__ == '__main__':
    client_port = 8000
    server_port = 8001
    try:
        client_port = int(sys.argv[1])
        server_port = int(sys.argv[2])
        file_path = sys.argv[3]
        server_addr = ('127.0.0.1', server_port)
        client = Client(client_port, file_path)
        client.listen_file_transfer(server_addr)
    except IndexError:
        print("Missing arguments")
        print("Format: \npython3 client.py [client port] [broadcast port] [path output]")

