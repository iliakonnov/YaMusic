print("Loading android_noti")

import os
from .ws import events
from .noti import prepare_noti

class Notifier:
    def __init__(self):
        self._pid = os.getpid()
        self._id = 'YaMusic'
        self._media = False

    def toggle(self):
        print('Toggle')
        self._media = not self._media
        self.send()

    def update(self):
        self.send()

    def send(self, update=False):
        from .kb import KeyboardHandlers
        from .signal_kb import mapping as sig_map
        summary, artists, position, timecode, total_time, outdated, actions = prepare_noti()

        make = lambda key: f'"kill -{sig_map[key]} {self._pid}"'
        buttons = ''
        if not self._media:
            #buttons += f'--action {make("on_toggle")} '
            buttons += f'--action {make("on_play")} '
            for i in range(1, 4):
                if 'dislike:Dislike' in actions:
                    text = 'Dislike'
                    action = 'on_dislike'
                    actions.remove('dislike:Dislike')
                elif 'like:Like' in actions:
                    text = 'Like'
                    action = 'on_like'
                    actions.remove('like:Like')
                elif 'next:Next' in actions:
                    text = 'Next'
                    action = 'on_next'
                    actions.remove('next:Next')
                else:
                    break
                sig = sig_map[action]
                buttons += (
                    f'--button{i} {text} '
                    f'--button{i}-action {make(action)} '
                )
        else:
            buttons += f'--action {make("on_toggle")} '
            buttons += (
                f'--type media '
                f'--media-next {make("on_next")} '
                f'--media-previous {make("on_prev")} '
                f'--media-pause {make("on_play")} '
                f'--media-play {make("on_like")} '
            )
            #if events._state['player']['isPlaying'] is True:
            #    buttons += f'--media-pause {make("on_play")} '
            #else:
            #    buttons += f'--media-play {make("on_play")} '

        cmd = ('termux-notification '
            f'--alert-once '
            f'--id {self._id} '
            f'--ongoing '
            f'-t "{summary}" '
            f'-c "{artists}" '
            f'--vibrate 0 '
        ) + buttons
        os.system(cmd)

noti = Notifier()
events.add_callback(noti.update)
print("\tLoaded android_noti")
