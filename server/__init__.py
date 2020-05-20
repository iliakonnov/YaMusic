import asyncio
import signal

PORT = 34438

def track_waiter(prop):
    def waiter(s):
        current = s['track']['current']
        if current is not None:
            return current[prop]
        return None
    return waiter

loop = asyncio.get_event_loop()
is_linux = True

from . import ws
from . import noti
from . import kb
from . import signal_kb
