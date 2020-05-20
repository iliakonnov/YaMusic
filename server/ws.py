print("Loading ws")
from . import loop, PORT
from .safe import SafeDict
from time import time
import json
import requests
import websockets
import asyncio
from pprint import pprint

q = asyncio.Queue()
def send(data):
    data = json.dumps(data)
    loop.call_soon_threadsafe(q.put_nowait, data)


class WebsocketEvents:
    def __init__(self):
        self._state = SafeDict()
        self._advert = None
        self._waiting = []
        self._callbacks = []
        self._lastUpd = 0

    def _update_cover(self, event, old_state):
        current = self._state['track']['current']
        if current is None or SafeDict.is_fake(current):
            return
        link = self._state['track']['current']['link']
        old_link = old_state['track']['current']['link']
        if not SafeDict.is_fake(link) and (SafeDict.is_fake(old_link) or old_link != link):
            cover = self._state['track']['current']['cover']
            assert not SafeDict.is_fake(cover)
            print(f'Updating cover by `{event}`: {old_link} -> {link}...', end='', flush=True)
            url = cover.replace('%%', '50x50')
            req = requests.get(f'http://{url}')
            with open('ya_cover.jpg', 'wb') as f:
                f.write(req.content)
            print(' Done!')

    def _update(self, event, old_state):
        if json.dumps(self._state.clone()) == json.dumps(old_state.clone()):
            return

        self._update_cover(event, old_state)
        for cb in self._callbacks:
            cb()

        new_waiting = []
        for i in self._waiting:
            getter, callback, expires = i
            old = getter(old_state)
            new = getter(self._state)
            if old != new:
                print(f'Waiter {callback} triggered by `{event}`')
                callback()
            elif expires < time():
                print(f'Waiter {callback} expired')
            else:
                new_waiting.append(i)
        self._waiting = new_waiting

    def ready(self):
        print('Ready!')

    def advert(self, state):
        if state is False:
            print('End ad')
            if self._advert is not None:
                send({'setVolume': self._advert})
            self._advert = None
        else:
            print('Start ad')
            send({'setVolume': 0})
            self._advert = self._state['player']['volume']

    def state(self, playerState):
        self._state['player'] = playerState

    def track(self, trackState):
        self._state['track'] = trackState

    def controls(self, controls):
        self._state['controls'] = controls

    def source(self, source):
        self._state['source'] = source

    def list(self, tracksList):
        self._state['list'] = tracksList

    def volume(self, volume):
        self._state['player']['volume'] = volume

    def speed(self, speed):
        self._state['player']['speed'] = speed

    def progress(self, progress):
        self._state['track']['progress'] = progress

    def full_state(self, full_state):
        self._state = SafeDict(full_state)

    def wait_change(self, getter, callback, wait_time):
        self._waiting.append((getter, callback, time() + wait_time))

    def add_callback(self, cb):
        self._callbacks.append(cb)

    def __call__(self, message):
        self._lastUpd = time()
        handler = getattr(self, message['event'])
        old_state = SafeDict(self._state.clone())
        if 'body' in message:
            handler(message['body'])
        else:
            handler()
        self._update(message['event'], old_state)

events = WebsocketEvents()

async def socket_handler(websocket, path):
    queue = asyncio.create_task(q.get(), name='queue')
    ws = asyncio.create_task(websocket.recv(), name='ws')
    while True:
        done, pending = await asyncio.wait([queue, ws], return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            try:
                if task.get_name() == 'queue':
                    queue = asyncio.create_task(q.get(), name='queue')
                    message = task.result()
                    print('Sending', message)
                    await websocket.send(message)
                if task.get_name() == 'ws':
                    ws = asyncio.create_task(websocket.recv(), name='ws')
                    message = json.loads(task.result())
                    events(message)
            except websockets.WebSocketException:
                raise
            except Exception as e:
                print('\n\nOoops', e)
                #pprint(events._state.clone())
                #await asyncio.sleep(1)
                raise

start_server = websockets.serve(socket_handler, "0.0.0.0", PORT)
loop.run_until_complete(start_server)
print("\tLoaded ws")
