from pynput.keyboard import Listener
from time import time, sleep
from os import environ
from sys import stdin, stderr, stdout
import asyncio
import threading
import json
import websockets
import requests
from pprint import pprint
from notify_send_py import NotifySendPy
from notify_send_py import Exit

loop = asyncio.get_event_loop()

""" TOOLS """

assert environ['DISPLAY'] == ':0'

def eprint(*args, **kwargs):
    kwargs['file'] = stderr
    print(*args, **kwargs)

""" WEBSOCKETS """

q = asyncio.Queue()
def send(data):
    data = json.dumps(data)
    loop.call_soon_threadsafe(q.put_nowait, data)

full_state = None

class SafeDict:
    def __init__(self, inner=None, fake=None):
        self._inner = {}
        self._fake = fake
        if inner is not None:
            for k, v in inner.items():
                self[k] = v

    def __contains__(self, key):
        return key in self._inner

    def __getitem__(self, key):
        if key in self._inner:
            return self._inner[key]
        else:
            return SafeDict(fake=(key, self))

    def __setitem__(self, key, value):
        self.de_fake()
        if isinstance(value, dict):
            self._inner[key] = SafeDict(value)
        else:
            self._inner[key] = value

    def __len__(self):
        return len(self._inner)

    def items(self):
        return self._inner.items()

    def is_fake(self):
        return self._fake is not None

    def de_fake(self):
        if self.is_fake():
            me, parent = self._fake
            parent[me] = self
            self._fake = None

    def clone(self):
        res = {}
        for k, v in self.items():
            if isinstance(v, SafeDict):
                res[k] = v.clone()
            else:
                res[k] = v
        return res


def is_fake(obj):
    if isinstance(obj, SafeDict):
        return obj.is_fake()
    return False


class WebsocketEvents:
    def __init__(self):
        self._state = SafeDict()
        self._advert = None
        self._waiting = []
        self._lastUpd = 0

    def _update_cover(self, event, old_state):
        current = self._state['track']['current']
        if current is None or is_fake(current):
            return
        link = self._state['track']['current']['link']
        old_link = old_state['track']['current']['link']
        if not is_fake(link) and (is_fake(old_link) or old_link != link):
            cover = self._state['track']['current']['cover']
            assert not is_fake(cover)
            print(f'Updating cover by `{event}`: {old_link} -> {link}...', end='', flush=True)
            url = cover.replace('%%', '50x50')
            req = requests.get(f'http://{url}')
            with open('/tmp/ya_cover.jpg', 'wb') as f:
                f.write(req.content)
            print(' Done!')

    def _update(self, event, old_state):
        self._update_cover(event, old_state)

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
                    eprint('Sending', message)
                    await websocket.send(message)
                if task.get_name() == 'ws':
                    ws = asyncio.create_task(websocket.recv(), name='ws')
                    message = json.loads(task.result())
                    events(message)
            except websockets.WebSocketException:
                raise
            except Exception as e:
                print('\n\nOoops', e)
                pprint(events._state.clone())
                await asyncio.sleep(1)

start_server = websockets.serve(socket_handler, "127.0.0.1", 34438)
loop.run_until_complete(start_server)

"""NOTIFICATIONS"""

def pretty_seconds(secs):
    secs = round(secs)
    return f'{secs // 60:02d}:{secs % 60:02d}'

class Notifier:
    def __init__(self):
        self._id = None
        self._expireAt = 0
        self._current = None
        self._lock = threading.Lock()

    def send(self, update=False):
        now = time()
        if update and self._expireAt > now:
            expirey = self._expireAt - now
        else:
            expirey = 3
            self._expireAt = now + expirey
        self._send(expirey=expirey*1000)

    def _send(self, expirey):
        noti = NotifySendPy()

        state = events._state
        track = state['track']['current']

        if time() - events._lastUpd > 3:
            outdated = '<span color="orange">Outdated</span>'
        else:
            outdated = ''

        if is_fake(track) or track is None:
            summary = 'Yandex.Nothing'
            artist = 'Nobody'
        elif events._advert is not None:
            summary = 'Yandex.Advert'
            artist = ''
        else:
            summary = ''
            if track['liked']:
                summary += '♥'
            if track['disliked']:
                summary += '⊘'
            if summary:
                summary = f'[{summary}] '
            summary += track['title']

            artists = track['artists']
            if len(artists) == 0:
                artist = 'unknown'
            else:
                artist = artists[0]['title']
                if len(artists) != 1:
                    artist += ' and {} others'.format(len(artists) - 1)
        timecode = state['player']['progress']['position']
        total_time = state['player']['progress']['duration']
        if state['source']['type'] != 'radio':
            position = '№{} / {}\n'.format(
                state['track']['index'] + 1,
                len(state['list']),
            )
        else:
            position = ''

        actions = []
        if state['controls']['prev']:
            actions.append('prev:Prev')
        if state['controls']['dislike']:
            actions.append('dislike:Dislike')
        if state['controls']['like']:
            actions.append('like:Like')
        if state['controls']['next']:
            actions.append('next:Next')
        # TODO: Blocking
        #actions = []

        try:
            self._id = noti.notify(
                summary=summary,
                body=(
                    f'{artist}\n'
                    f'\n'
                    f'{position}'
                    f'{pretty_seconds(timecode)}/{pretty_seconds(total_time)}'
                    f'\t(-{pretty_seconds(total_time-timecode)})\n'
                    f'{outdated}'
                ),
                icon='file:///tmp/ya_cover.jpg',
                expirey=expirey,
                replaces_id=self._id,
                actions=actions,
            )
        except Exception as e:
            print('FAIL notifying', e)
            try:
                self._id = noti.notify(
                    summary='Yandex.Music',
                    body=f'Fail notifying',
                    replaces_id=self._id
                )
            except:
                print('Double fail!')
            return
        with self._lock:
            if self._current is not None:
                self._current.quit()
        if actions:
            threading.Thread(
                target=self._wait,
                args=(noti, self._id),
                daemon=True
            ).start()

    def _wait(self, noti, noti_id):
        cnt = 0
        while self._current is not None:
            print('!', end='', flush=True)
            sleep(0.1)
            cnt += 1
            if cnt > 5:
                print('Waiter failed to start')
                return
        with self._lock:
            assert self._current is None
            self._current = noti.loop
        noti.loop.run()
        with self._lock:
            assert self._current is noti.loop
            self._current = None
        if self._id != noti_id:
            return
        msg = {}
        waiters = set()
        for action in noti.actions_out:
            if action == 'prev':
                msg['prev'] = None
                waiters.add('link')
            elif action == 'next':
                msg['next'] = None
                waiters.add('link')
            elif action == 'dislike':
                msg['toggleDislike'] = None
                waiters.add('disliked')
            elif action == 'like':
                msg['toggleLike'] = None
                waiters.add('liked')
        for prop in waiters:
            events.wait_change(
                track_waiter(prop),
                lambda: self.send(update=True),
                3
            )
        print(f'Callback: {noti.actions_out} -> {msg}')
        if msg:
            send(msg)

noti = Notifier()

""" KEYBOARD """

def track_waiter(prop):
    def waiter(s):
        current = s['track']['current']
        if current is not None:
            return current[prop]
        return None
    return waiter


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

    def on_fallback(self, key):
        pass

    handlers = {
        269025044: on_play,
        269025045: on_stop,
        269025046: on_prev,
        269025047: on_next,
        269025073: on_like,
        269025068: on_dislike,
    }

    def __call__(self, key):
        handler = None
        if hasattr(key, 'vk'):
            handler = self.handlers.get(key.vk)
        if handler is None:
            return self.on_fallback(key)
        return handler(self)
keyboard = Listener(on_press=KeyboardHandlers())
keyboard.start()

loop.run_forever()
