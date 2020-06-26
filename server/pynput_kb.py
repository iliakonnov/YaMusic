print("Loading pynput_kb")
from .kb import KeyboardHandlers
from pynput.keyboard import Listener

kb = KeyboardHandlers()

mapping = {
    269025044: kb.on_play,
    269025045: kb.on_stop,
    269025046: kb.on_prev,
    269025047: kb.on_next,
    269025073: kb.on_like,
    269025068: kb.on_dislike,
}

def handler(key):
    handler = None
    if hasattr(key, 'vk'):
        handler = mapping.get(key.vk)
    if handler is not None:
        return handler()
keyboard = Listener(on_press=handler)
keyboard.start()
print("\tLoaded pynput_kb")
