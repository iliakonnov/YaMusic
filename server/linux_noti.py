print("Loading linux_noti")
from . import track_waiter
import threading
import os
from time import time, sleep
from .ws import events
from .noti import prepare_noti
from .notify_send_py import NotifySendPy

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
        summary, artist, position, timecode, total_time, outdated, actions = prepare_noti()
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
                icon=f'file://{os.path.abspath(os.getcwd())}/ya_cover.jpg',
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
print("\tLoaded linux_noti")
