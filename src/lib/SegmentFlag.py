# Constant Values
from .Constant import *

class SegmentFlag:
    
    def __init__(self, flag: list) -> None:
        if isinstance(flag, int):
            # Convert bitfield to boolean flags
            self.fin = bool(flag & FIN_FLAG)
            self.syn = bool(flag & SYN_FLAG)
            self.psh = bool(flag & PSH_FLAG)
            self.ack = bool(flag & ACK_FLAG)
        elif isinstance(flag, list):
            self.fin = bool(flag[0])
            self.syn = bool(flag[1])
            self.psh = bool(flag[2])
            self.ack = bool(flag[3])

    def __str__(self):
        return f"SYN={self.syn}, ACK={self.ack}, FIN={self.fin}"

    def get_flag_value(self) -> int:
        # Return flag bytes (dalam integer)
        flag = DEFAULT_FLAG
        flag |= (FIN_FLAG if self.fin else DEFAULT_FLAG)
        flag |= (SYN_FLAG if self.syn else DEFAULT_FLAG)
        flag |= (PSH_FLAG if self.psh else DEFAULT_FLAG)
        flag |= (ACK_FLAG if self.ack else DEFAULT_FLAG)
        return flag
    
    def is_default_flag(self) -> bool:
        return not (self.syn or self.ack or self.fin)
    
    def is_syn_flag(self) -> bool:
        return self.syn

    def is_psh_flag(self) -> bool:
        return self.psh
    
    def is_ack_flag(self) -> bool:
        return self.ack
    
    def is_fin_flag(self) -> bool:
        return self.fin
    
    def is_syn_ack_flag(self) -> bool:
        return self.syn and self.ack
    
    def is_fin_ack_flag(self) -> bool:
        return self.fin and self.ack
    
    def is_syn_fin_flag(self) -> bool:
        return self.syn and self.fin

if __name__ == "__main__":
    seg = SegmentFlag(0x02)
    print(seg.get_flag_value())
    
    