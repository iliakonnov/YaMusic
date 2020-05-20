print("Loading signal_kb")
from .kb import KeyboardHandlers
import signal
import os

kb = KeyboardHandlers()

def wrap(callback):
    def handler(signum, frame):
        return callback()
    return handler

mapping = {
   'on_play'   : signal.SIGRTMAX-1,
   'on_stop'   : signal.SIGRTMAX-2,
   'on_prev'   : signal.SIGRTMAX-3,
   'on_next'   : signal.SIGRTMAX-4,
   'on_like'   : signal.SIGRTMAX-5,
   'on_dislike': signal.SIGRTMAX-6,
   'on_toggle' : signal.SIGRTMAX-7
}

for cb, sig in mapping.items():
    cb = getattr(kb, cb)
    signal.signal(sig, wrap(cb))

print(f"\tLoaded signal_kb (pid={os.getpid()})")
