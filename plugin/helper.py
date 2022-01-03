import websocket
import json
from pathlib import Path
from tempfile import gettempdir
import os
from time import time
from functools import wraps


discord = "wss://gateway.discord.gg/?v=6&encoding=json"

CACHE_TIME = 600
DISCORD_TIMEOUT = 15

def cache(file_name, cache_time=CACHE_TIME):
    """
    Cache decorator
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_file = Path(gettempdir(), file_name)
            if not cache_file.exists() or time() - cache_file.stat().st_mtime > cache_time or cache_file.stat().st_size == 0:
                data = func(*args, **kwargs)
                if len(data) != 0 or data is not None:
                    with open(cache_file, 'w') as f:
                        json.dump(data, f)
                return data
            else:
                with open(cache_file, 'r') as f:
                    return json.load(f)
        return wrapper
    return decorator
    
@cache('discord_guilds.json')
def _get_discord_guilds(token):
    """
    Returns a list of all guilds the user is in
    """
    guilds = None
    ws = websocket.create_connection(discord)
    ws.send(json.dumps({
        'op': 2,
        'd': {
            'token': token,
            'properties': {
                '$os': 'linux',
                '$browser': 'discord.py',
                '$device': 'discord.py'
            },
            'compress': False,
            'large_threshold': 250,
            'shard': [0, 1]
        }
    }))

    start = time()
    while True:
        resp = json.loads(ws.recv())
        if resp['t'] == 'READY':
            guilds = resp['d']['guilds']
            break
        elif time() - start > DISCORD_TIMEOUT:
            raise ConnectionTimeout()
    ws.close()

    return guilds

def get_guilds(token):
    """
    Returns a list of all guilds the user is in
    """
    for guilds in _get_discord_guilds(token):
        yield Guild(guilds)

class Guild(object):

    def __init__(self, data):
        self._data = data
        for key, value in data.items():
            setattr(self, key, value)

    def icon_url(self):
        return f"https://cdn.discordapp.com/icons/{self.id}/{self.icon}.png"

    def get_channels(self):
        channels = []
        for channel in self._data['channels']:
            if channel['type'] == 0: 
                channels.append(Channel(self, channel))
        return channels

class Channel(object):

    def __init__(self, guild, data):
        self._guild = guild
        self._data = data
        self.topic = None
        self.parent_id = None
        for key, value in data.items():
            setattr(self, key, value)

    def icon_url(self):
        return self._guild.icon_url()

    def uri(self):
        return f"discord://discord.com/channels/{self._guild.id}/{self.id}"

    def category(self):
        for category in self._guild._data['channels']:
            if category['id'] == self.parent_id:
                return category['name']
        return None

class ConnectionTimeout(Exception):
    
    def __init__(self):
        self.message = 'Connection timed out'