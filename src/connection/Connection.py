from datetime import datetime
import time


class Connection:
    def __init__(self, from_ip, from_port, to_ip, to_port, send_seq=0, recv_seq=0, current_index = 0):
        self.from_ip = from_ip
        self.from_port = from_port
        self.to_ip = to_ip
        self.to_port = to_port

        self.last_heartbeat = datetime.now()

        self.current_index_message = current_index

        self.send_seq = send_seq
        self.recv_seq = recv_seq

        self.is_connected = False

        self.send_window = {}
        self.acknowledged = set()
        self.last_activity = time.time()

    def get_current_index(self):
        return self.current_index_message
    
    def increase_index(self) -> None:
        self.current_index_message += 1