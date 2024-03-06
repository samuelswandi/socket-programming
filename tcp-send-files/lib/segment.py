import struct
import math

# Constants
SYN_FLAG = 0b0010
ACK_FLAG = 0b1000
FIN_FLAG = 0b0001

class Segment:
    # -- Internal Function --

    # maximum segment size = 2^15 = 32768
    MDS = 32756
    """
    SEG_FORMAT explanation:
    sequence num    = 4 bytes,
    ack num         = 4 bytes
    flag            = 1 byte,
    padding         = 1 byte,
    checksum        = 2 bytes
    """
    SEG_FORMAT = 'i i b x H '

    def __init__(self, seq_number=0, ack_number=0, flag=0, payload=b'0', check_sum=0):
        self.seq_number = seq_number
        self.ack_number = ack_number
        self.check_sum = check_sum
        self.flag = flag

        if len(payload) > self.MDS:
            raise Exception('Packet content is too long')
        self.payload = payload
        self.SEG_FORMAT += f'{len(self.payload)}s'

        if self.check_sum == 0:
            self.check_sum = self.__calculate_checksum()

    def __str__(self):
        output = ""
        output += f"Sequence number: {self.seq_number}\n"
        output += f"Acknowledge number: {self.ack_number}\n"
        output += f"Flag: {self.flag}\n"
        output += f"Check sum: {self.check_sum}\n"
        output += f"Payload: {self.payload}\n"
        return output

    def __calculate_checksum(self):
        # Calculate checksum of this using 16-bit one's complement

        #initialize checksum 
        checksum = 0

        #add sequence number and ack number (split into two 2 bytes)
        checksum += self.seq_number
        checksum &= 0xFFFF
        checksum += self.ack_number 
        checksum &= 0xFFFF
        checksum += (self.seq_number >> 16)
        checksum &= 0xFFFF
        checksum += (self.ack_number >> 16)
        checksum &= 0xFFFF

        #add flag to checksum
        checksum += self.flag
        #add payload to checksum
        for i in range(0, len(self.payload), 2):
            #if payload is odd number of bytes, add padding byte
            if i == len(self.payload) - 1:
                checksum += self.payload[i] << 8
                checksum &= 0xFFFF
            else:
                checksum += self.payload[i] + (self.payload[i+1] << 8)
                checksum &= 0xFFFF

        return checksum ^ 0xFFFF & 0xFFFF


    """
    Setter
    """
    def set_header(self, seq_number=0, ack_number=0, flag=0):
        self.seq_number = seq_number
        self.ack_number = ack_number
        self.flag = flag
        self.check_sum = self.__calculate_checksum

    def set_payload(self, payload : bytes):
        if len(payload) > self.MDS:
            raise Exception('Packet content is too long')

        self.payload = payload
        self.check_sum = self.__calculate_checksum

    def set_flag(self, flag_list : list):
        for flag in flag_list:
            self.flag |= flag
        self.check_sum = self.__calculate_checksum


    """
    Getter
    """
    def get_flag(self) -> bytes:
        return self.flag

    def get_header(self) -> dict:
        header = {}
        header['seq_number'] = self.seq_number
        header['ack_number'] = self.ack_number
        header['flag'] = self.flag
        header['check_sum'] = self.check_sum
        return header

    def get_payload(self) -> bytes:
        return struct.pack(f'{len(self.payload)}s', self.payload)


    """
    Marshalling
    """
    def set_from_bytes(self, src : bytes):
        SEG_FORMAT = 'i i b x h '
        SEG_FORMAT += f"{len(src)-12}s"
        (self.seq_number,
        self.ack_number,
        self.flag,
        self.check_sum,
        self.payload) = struct.unpack(SEG_FORMAT, src)
        return self

    def get_bytes(self) -> bytes:
        return struct.pack(
            self.SEG_FORMAT,
            self.seq_number,
            self.ack_number,
            self.flag,
            self.check_sum,
            self.payload
        )


    """
    Checksum
    """
    def valid_checksum(self) -> bool:
        # Use __calculate_checksum() and check integrity of this object
        temp = self.check_sum
        temp += self.seq_number
        temp &= 0xFFFF
        temp += self.ack_number
        temp &= 0xFFFF
        temp += (self.seq_number >> 16) 
        temp &= 0xFFFF
        temp += (self.ack_number >> 16) 
        temp &= 0xFFFF
        temp += self.flag

        for i in range(0, len(self.payload), 2):
            if i == len(self.payload) - 1:
                temp += self.payload[i] << 8
                temp &= 0xFFFF
            else:
                temp += self.payload[i] + (self.payload[i+1] << 8) 
                temp &= 0xFFFF
        return temp == 0xFFFF

