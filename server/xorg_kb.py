print("Loading xorg_kb")

from Xlib.display import Display
from Xlib import XK
from Xlib import X
from threading import Thread

XK.load_keysym_group('xf86')

from .kb import KeyboardHandlers
kb = KeyboardHandlers()

mapping = {
    XK.XK_XF86_AudioPlay: kb.on_play,
    XK.XK_XF86_AudioStop: kb.on_stop,
    XK.XK_XF86_AudioPrev: kb.on_prev,
    XK.XK_XF86_AudioNext: kb.on_next,
    (XK.XK_XF86_AudioPlay, X.ShiftMask): kb.on_like,
    (XK.XK_XF86_AudioStop, X.ShiftMask): kb.on_dislike,
}

class Listener(Thread):
    def __init__(self):
        super().__init__()
        display = Display()
        self.root = display.screen().root
        self.handlers = {}

        for key, handler in mapping.items():
            if not isinstance(key, int):
                key, mask = key
            else:
                mask = 0
            keycode = display.keysym_to_keycode(key)
            self.root.grab_key(keycode, mask, False, X.GrabModeAsync, X.GrabModeAsync)
            self.handlers[(keycode, mask)] = handler

    def run(self):
        while True:
            event = self.root.display.next_event()
            if event.type == X.KeyPress:
                keycode = event.detail
                mask = event.state
                handler = self.handlers.get((keycode, mask))
                if handler is not None:
                    handler()

l = Listener()
l.daemon = True
l.start()

print("\tLoaded xorg_kb")
