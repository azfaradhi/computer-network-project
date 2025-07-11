from struct import unpack, pack
from .Constant import *
from .SegmentFlag import *

from typing import Dict, Union

class Segment:
    def __init__(self, username: str, flag: list, seq_num: int = 0, ack_num: int = 0, data: bytes = b"", checksum: int = 0) -> None:
        # Initalize segment
        self.header: Dict[str, Union[int, SegmentFlag]] = {
            'srcPort'  : 0,
            'dstPort'  : 0,
            'seqNumber': seq_num,
            'ackNumber': ack_num,
            'flag'     : SegmentFlag(flag),
            'checksum' : checksum,
            'username' : username
        }
        
        self.data = data  # payload
        self.update_checksum()

    def __str__(self):
        # Optional, override this method for easier print(segmentA)
        output = ""
        output += f"{'Source port':24} | {self.header['srcPort']}\n"
        output += f"{'Destination port':24} | {self.header['dstPort']}\n"
        output += f"{'Sequence number':24} | {self.header['seqNumber']}\n"
        output += f"{'Acknowledgement number':24} | {self.header['ackNumber']}\n"
        output += f"{'Checksum':24} | {self.header['checksum']}\n"
        output += f"{'Flag':24} | {SegmentFlag(self.header['flag']).get_flag_value()}\n"
        output += f"{'Payload':24} | {self.data}\n"
        return output

    # -- Setter --
    def set_header(self, header : dict):
        # Set header from dictionary
        self.header = header
        self.update_checksum()

    def set_data(self, data: bytes):
        if len(data) > 64:
            raise ValueError("Payload too large. The maximum is 64 bytes.")
        self.data = data
        self.update_checksum()
    
    def set_seq_number(self, seq_number : int):
        # Set sequence number
        self.header['seqNumber'] = seq_number
        self.update_checksum()
    
    def set_ack_number(self, ack_number : int):
        # Set acknowledgement number
        self.header['ackNumber'] = ack_number
        self.update_checksum()

    def set_flag(self, flag_list : list):
        # Set flag from list of flag (SYN, ACK, FIN)
        self.header['flag'] = SegmentFlag(flag_list)
        self.update_checksum()


    # ------------ Getter ------------
    def get_flag(self) -> SegmentFlag:
        # return flag in segmentflag
        return self.header['flag']

    def get_header(self) -> dict:
        # Return header in dictionary form
        return self.header

    def get_data(self) -> bytes:
        # Return payload in bytes
        return self.data
    
    def get_username(self) -> str:
        return self.header['username']

    def set_from_bytes(self, src: bytes):
        header_bytes = src[:15]
        header_tup = unpack('!HHIIBH', header_bytes)
        self.header = {
            'srcPort': header_tup[0],
            'dstPort': header_tup[1],
            'seqNumber': header_tup[2],
            'ackNumber': header_tup[3],
            'flag': header_tup[4],
            'checksum': header_tup[5],
        }
        self.data = src[15:]

        # self.update_checksum()

    def get_bytes(self) -> bytes:
        # Convert this object to pure bytes
        header_bytes = pack(
            '!HHIIBH',
            self.header['srcPort'],
            self.header['dstPort'],
            self.header['seqNumber'],
            self.header['ackNumber'],
            self.header['flag'].get_flag_value(), 
            self.header['checksum']
        )
        username_str = self.header.get('username', '')
        username_bytes = username_str.encode('utf-8')[:10]         # max 10 bytes
        username_bytes = username_bytes.ljust(10, b'\x00')         # pad with nulls if shorter

        return header_bytes + username_bytes + self.data

    def get_bytes_no_checksum(self) -> bytes:
        header_bytes = pack('!HHIIB',
            self.header['srcPort'],
            self.header['dstPort'],
            self.header['seqNumber'],
            self.header['ackNumber'],
            self.header['flag'].get_flag_value(),
        )
        username_str = self.header.get('username', '')
        username_bytes = username_str.encode('utf-8')[:10]
        username_bytes = username_bytes.ljust(10, b'\x00')  # pad with null bytes

        return header_bytes + username_bytes + self.data


    # -- Checksum --
    def valid_checksum(self) -> bool:
        # Use __calculate_checksum() and check integrity of this object
        return self.__calculate_checksum() == self.header['checksum']
    
    def __calculate_checksum(self) -> int:
        # Calculate checksum here, return checksum result
        sum = 0
        data_bytes = self.get_bytes_no_checksum()

        if (len(data_bytes) % 2 != 0):
            data_bytes += b'\x00'
            
        for i in range(0, len(data_bytes), 2):
            sum += int.from_bytes(data_bytes[i:i+2], byteorder='big')

        while sum >> 0xffff:
            sum = (sum & 0xffff) + (sum >> 16)

        return ~sum & 0xffff

    def update_checksum(self):
        checksum = self.__calculate_checksum()
        checksum &= 0xffff
        self.header['checksum'] = checksum

    @staticmethod
    def syn(
        username: str = '',
        seq_num:  int = 0,
        ack_num:  int = 0
    ): return Segment(username, [False, True, False, False], seq_num, ack_num, b"", 0)
    
    @staticmethod
    def ack(
        username: str = '',
        seq_num:  int = 0, 
        ack_num:  int = 0
    ): return Segment(username, [False, False, False, True], seq_num, ack_num, b"", 0)
    
    @staticmethod
    def syn_ack(
        username: str = '',
        seq_num:  int =  0, 
        ack_num:  int = 0
    ): return Segment(username, [False, True, False, True], seq_num, ack_num, b"", 0)
  
    @staticmethod
    def fin(
        username: str = '',
        seq_num:  int =  0, 
        ack_num:  int = 0
    ): return Segment(username, [True, False, False, False], seq_num, ack_num, b"", 0)
    
    @staticmethod
    def fin_ack(
        username: str = '',
        seq_num:  int =  0, 
        ack_num:  int = 0
    ): return Segment(username, [True, False, False, True], seq_num, ack_num, b"", 0)
    
    @staticmethod
    def psh(
        username: str = '',
        seq_num:  int =  0, 
        ack_num:  int = 0
    ): return Segment(username, [False, False, True, False], seq_num, ack_num, b"", 0)
    
    @staticmethod
    def from_bytes(data: bytes):
        src_port, dst_port, seq_num, ack_num, flag, checksum = unpack("!HHIIBH", data[:15])
        username_bytes = data[15:25]
        username = username_bytes.rstrip(b'\x00').decode('utf-8', errors='ignore')

        payload = data[25:]
        segment = Segment(username, flag, seq_num, ack_num, payload, checksum)
        segment.header['srcPort'] = src_port
        segment.header['dstPort'] = dst_port
        return segment, segment.valid_checksum()

class SegmentError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

if __name__ == '__main__':
    segment = Segment()
    segment.header['seqNumber'] = 1
    segment.header['ackNumber'] = 2
    segment.header['flag'] = SegmentFlag(SYN_FLAG)
    segment.data = b"Hello World"
    segment.update_checksum()
    print(segment.calculate_checksum())
    if segment.valid_checksum():
        print("Checksum valid")
    else:
        print("Checksum invalid")
    print(segment.get_bytes_no_checksum().hex())
    print(segment.get_bytes().hex())
