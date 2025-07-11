import datetime
from lib.Constant import MAX_WIDTH
import textwrap

class MessageInfo:
    def __init__(self, fromName: str, time: datetime, msg: str):
        self.username = fromName
        self.time = time
        self.msg = msg
    
    def __str__(self):
        hourFormat = "AM"
        if self.time.hour >= 12:
            hourFormat = "PM"
        hour = self.time.hour if self.time.hour <= 12 else self.time.hour - 12

        message_content = f"{self.username} [{hour}:{self.time.minute:02d} {hourFormat}] : {self.msg}"
        
        wrapped_lines = textwrap.wrap(message_content, width=MAX_WIDTH - 4)
        
        if not wrapped_lines:
            wrapped_lines = [message_content]
        
        actual_width = min(MAX_WIDTH, max(len(line) for line in wrapped_lines) + 4)
        
        formatted_lines = []
        for line in wrapped_lines:
            padded_line = f"│ {line.ljust(actual_width - 4)}"
            formatted_lines.append(padded_line)
        
        result = formatted_lines
        return "\n".join(result)
    
    def get_msg(self) -> str:
        return self.msg
    
    def get_username(self) -> str:
        return self.username