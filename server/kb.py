print("Loading kb")
from .ws import send, events
from .noti import noti
from . import is_linux, track_waiter

class KeyboardHandlers:
    def on_play(self):
        send({'togglePause': None})

    def on_stop(self):
        #pprint(events._state.clone())
        #print('ADVERT', events._advert)
        noti.send(update=True)

    def on_next(self):
        events.wait_change(
            track_waiter('link'),
            noti.send,
            3
        )
        send({'next': None})
        noti.send()

    def on_prev(self):
        events.wait_change(
            track_waiter('link'),
            lambda: noti.send(update=True),
            3
        )
        send({'prev': None})
        noti.send()

    def on_like(self):
        events.wait_change(
            track_waiter('liked'),
            lambda: noti.send(update=True),
            3
        )
        send({'toggleLike': None})
        noti.send()

    def on_dislike(self):
        events.wait_change(
            track_waiter('disliked'),
            lambda: noti.send(update=True),
            3
        )
        send({'toggleDislike': None})
        noti.send()

    def on_toggle(self):
        noti.toggle()

if is_linux:
    from . import xorg_kb
else:
    from . import pynput_kb

print("\tLoaded kb")
