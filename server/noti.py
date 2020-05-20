print("Loading noti")
from time import time
from .safe import SafeDict
from . import is_linux
from .ws import events

def prepare_noti():
    state = events._state
    track = state['track']['current']

    if time() - events._lastUpd > 3:
        outdated = '<span color="orange">Outdated</span>'
    else:
        outdated = ''

    timecode = 0
    total_time = 0
    position = ''
    if SafeDict.is_fake(track) or track is None:
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

    actions = []
    if state['controls']['prev']:
        actions.append('prev:Prev')
    if state['controls']['dislike']:
        actions.append('dislike:Dislike')
    if state['controls']['like']:
        actions.append('like:Like')
    if state['controls']['next']:
        actions.append('next:Next')
    return summary, artist, position, timecode, total_time, outdated, actions

if is_linux:
    from .linux_noti import noti
else:
    from .android_noti import noti
print("\tLoaded noti")
