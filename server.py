from lib.connection import Connection
from lib.segment import Segment
import sys
import os
import socket
import math

SYN_FLAG = 0b0010
ACK_FLAG = 0b1000
FIN_FLAG = 0b0001
MDS = 32756

class Server:
    def __init__(self, port, file_path):
        self.server = Connection('127.0.0.1', port)
        self.file_path = file_path
        self.client_list = []

        # If file does not exist, terminate the program
        if not os.path.exists(self.file_path):
            raise Exception("File does not exist!\nFilename: %s" % self.file_path)

    def get_all_client(self):
        return self.client_list


    def listen_for_clients(self):
        print("[!] Listening to broadcast address for clients")


        """
        Listening to clients
        """
        while True:
            request, client_addr = self.server.listen_single_segment()
            print(f"[!] Received request from {client_addr[0]}:{client_addr[1]}")
            self.client_list.append(client_addr)
            text = input('[?] Listen more? (y/n): ')
            if text != 'y': break

        return

    def start_file_transfer_all_client(self):
        for index in range(len(self.client_list)):
            """
            Commencing three way handshake to client with index given
            """
            print(f"[!] [Client {index+1}] [File Transfer] Commencing file transfer")
            established = self.three_way_handshake(index+1, self.client_list[index])
            while not established:
                print(f"[!] [Client {index+1}] Handshake failed")
                retry = input(f'[?] [Client {index+1}] Want to retry handshake? (y/n): ')
                if retry == 'n': break
                established = self.three_way_handshake(index+1, self.client_list[index])

            if not established:
                print(f"[!] [Client {index+1}] [File Transfer] File transfer failed")
                return False

            """
            Starting file transfer
            """
            print(f"[!] [Client {index+1}] [File Transfer] Starting...")
            self.send_file(index, self.client_list[index])

            # If it's already the last client then file already sent to all user
            if index+2 > len(self.client_list):
                print(f"[!] [File Transfer] File successfully sent to all clients.")
                break

            """
            Waiting for all ACK segment from client before to done
            """
            self.server.set_timeout(10)
            try:
                while True : self.server.listen_single_segment()[0]
            except socket.timeout:
                pass


    def start_file_transfer(self):
        """
        Choosing client
        """
        print("\nClient list")
        for i in range(len(self.client_list)):
            print(f'{i+1}. {self.client_list[i][0]}:{self.client_list[i][1]}')
        index = int(input("\n[?] Choose client to commence file transfer: "))
        index -= 1


        """
        Commencing three way handshake to client with index given
        """
        print(f"[!] [Client {index+1}] [File Transfer] Commencing file transfer")
        established = self.three_way_handshake(index+1, self.client_list[index])
        while not established:
            print(f"[!] [Client {index+1}] Handshake failed")
            retry = input(f'[?] [Client {index+1}] Want to retry handshake? (y/n): ')
            if retry == 'n': break
            established = self.three_way_handshake(index+1, self.client_list[index])

        if not established:
            print(f"[!] [Client {index+1}] [File Transfer] File transfer failed")
            return False

        """
        Starting file transfer
        """
        print(f"[!] [Client {index+1}] [File Transfer] Starting...")
        return self.send_file(index, self.client_list[index])


    def send_file(self, index, client_addr):
        print(f"[!] [Client {index+1}] [File Transfer] Initializing file transfer to client")

        """
        Divide data binary to maximum data size in segment with optimized seek
        """
        data_list = []
        total_chunk = math.ceil(os.path.getsize(self.file_path) // MDS) + 1
        with open(self.file_path, 'rb') as f:
            for i in range(total_chunk):
                f.seek(32756*i)
                data_list.append(f.read(MDS))


        """
        Create seq_base number and seq_max number
        Then send segment by request
        """
        seq_base = 0
        window_size = 3
        seq_max = window_size
        for i in range(seq_base, min(seq_max, total_chunk)):
            segment = Segment(seq_number=i, payload=data_list[i])
            self.server.send_data(segment.get_bytes(), client_addr)
            print(f"[!] [Client {index+1}] [File Transfer] [Segment SEQ={i}] Sent")


        """
        ARQ Go Back-N
        """
        retry_header = None
        retry_handshake = False
        self.server.set_timeout(2)
        while seq_base < total_chunk:
            try:
                res = self.server.listen_single_segment()[0]
                segment = Segment().set_from_bytes(res)
                seg_header = segment.get_header()
                req_num = seg_header['ack_number']

                # if client want to retry handshake
                if seg_header['flag'] == (SYN_FLAG | ACK_FLAG):
                    retry_handshake = True
                    retry_header = seg_header
                    break

                if seg_header['flag'] == ACK_FLAG:
                    if req_num == seq_base:
                        seq_base += 1
                        seq_max += 1
                        print(f"[!] [Client {index+1}] [File Transfer] [Segment SEQ={req_num}] Acked, New sequence base: {seq_base}")

                    elif req_num > seq_base:
                        seq_max = (seq_max - seq_base) + req_num
                        seq_base = req_num
                        print(f"[!] [Client {index+1}] [File Transfer] [Segment SEQ={req_num}] Acked, New sequence base: {seq_base}")

                    else:
                        print(f"[!] [Client {index+1}] [File Transfer] [Segment SEQ={req_num}] Wrong ACK number")

            except socket.timeout:
                print(f"[!] [Client {index+1}] [File Transfer] Did not receive ACK in allocated timeout!")

            for i in range(seq_base, min(seq_max, total_chunk)):
                segment = Segment(seq_number=i, payload=data_list[i])
                self.server.send_data(segment.get_bytes(), client_addr)
                print(f"[!] [Client {index+1}] [File Transfer] [Segment SEQ={i}] Sent")


        """
        If client requested for retry handshake
        """
        if retry_handshake:
            print(f"[!] [Client {index+1}] [File Transfer] SYN_ACK Flag received. Retry handshake")
            self.three_way_handshake(index + 1, client_addr, False, retry_header)
            self.send_file(index, client_addr)


        """
        Sending FIN segment then file successfully delivered
        """
        self.server.send_data(Segment(flag=FIN_FLAG).get_bytes(), client_addr)
        print(f"[!] [Client {index+1}] [File Transfer] Sending FIN segment")

        while True:
            segment = self.server.listen_single_segment()[0]
            seg_header = Segment().set_from_bytes(segment).get_header()
            if seg_header['flag'] == ACK_FLAG or seg_header['flag'] == FIN_FLAG:
                break

            print(f"[!] [Client {index+1}] [File Transfer] FIN segment requested")
            self.server.send_data(Segment(flag=FIN_FLAG).get_bytes(), client_addr)
            print(f"[!] [Client {index+1}] [File Transfer] Sending FIN segment")

        print(f"[!] [Client {index+1}] [File Transfer] File successfully delivered")
        return True


    def three_way_handshake(self, client_index, client_addr, starting=True, retry_header=None) -> bool:
        print(f"[!] [Client {client_index}] [Handshake] Server handshake started")


        self.server.set_timeout(10)
        while True:
            try:
                # if starting three way handshake then send SYN to client
                if starting:
                    print(f"[!] [Client {client_index}] [Handshake] Sending SYN to {client_addr[0]}:{client_addr[1]}")
                    seq_number = 0
                    syn_segment = Segment(seq_number=seq_number,
                                        ack_number=0,
                                        flag=SYN_FLAG)
                    self.server.send_data(syn_segment.get_bytes(), client_addr)
                    print(f'[!] [Client {client_index}] [Handshake] SYN Segment delivered')


                    # Waiting for SYN_ACK segment from client
                    print(f"[!] [Client {client_index}] [Handshake] Waiting SYN_ACK from {client_addr[0]}:{client_addr[1]}")
                    self.server.set_timeout(5)
                    syn_ack_segment, syn_ack_client_addr = self.server.listen_single_segment()


                    # validate ACK address
                    if syn_ack_client_addr != client_addr:
                        raise ValueError(f"Wrong client connection. Expected {client_addr[0]}:{client_addr[1]}, got {syn_ack_client_addr[0]}:{syn_ack_client_addr[1]}")


                    # If SYN_ACK received, then send ACK segment
                    syn_ack_seg_header = Segment().set_from_bytes(syn_ack_segment).get_header()
                    if syn_ack_seg_header['flag'] == (SYN_FLAG | ACK_FLAG):
                        print(f"[!] [Client {client_index}] [Handshake] SYN_ACK Segment received")

                        # Sending ACK segment to client
                        print( f"[!] [Client {client_index}] [Handshake] Sending ACK to {client_addr[0]}:{client_addr[1]}")
                        ack_segment = Segment(seq_number=syn_ack_seg_header['ack_number'],
                                            ack_number=syn_ack_seg_header['seq_number']+1,
                                            flag=ACK_FLAG)
                        self.server.send_data(ack_segment.get_bytes(), client_addr)
                        print(f'[!] [Client {client_index}] [Handshake] ACK Segment delivered')
                        break

                # if retrying handshake, then only need to send ACK
                else:
                    # Sending ACK segment to client
                    print( f"[!] [Client {client_index}] [Handshake] Sending ACK to {client_addr[0]}:{client_addr[1]}")
                    ack_segment = Segment(seq_number=retry_header['ack_number'],
                                        ack_number=retry_header['seq_number']+1,
                                        flag=ACK_FLAG)
                    self.server.send_data(ack_segment.get_bytes(), client_addr)
                    print(f'[!] [Client {client_index}] [Handshake] ACK Segment delivered')
                    break

            except socket.timeout:
                print(f'[!] [Client {client_index}] [Handshake] Server timeout')
                print(f'[!] [Client {client_index}] [Handshake] Retry handshake')
                break

            except Exception as e:
                print(f'[!] [Client {client_index}] [Handshake] {e.args[0]}')
                print(f'[!] [Client {client_index}] [Handshake] Connection failed')
                break

        # Connection established
        print(f"[!] [Client {client_index}] [Handshake] Connection established to {client_addr[0]}:{client_addr[1]}")
        self.client_addr = client_addr
        return True


if __name__ == '__main__':
    try:
        port = int(sys.argv[1])
        file_path = (sys.argv[2])
        server = Server(port, file_path)

        server.listen_for_clients()
        while True:
            print('\n==== Start file transfer! ==== ')
            print('Client List:')
            for i,v in enumerate(server.get_all_client()):
                print(f'{i+1}. {v[0]}:{v[1]}')

            print('\nList of command for file transfer:')
            print('1. One client')
            print('2. All client')
            print('3. Exit program\n')

            start = input(f'[?] Input command: ')
            if start == '1':
                server.start_file_transfer()

            elif start == '2':
                server.start_file_transfer_all_client()

            else:
                print(f"[!] Program exited")
                break
    except IndexError as e:
        print(e)
        print("Missing arguments")
        print("Format: \npython3 client.py [client port] [broadcast port]")
    except Exception as e:
        print(e)

