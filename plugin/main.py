from tempfile import gettempdir
from pathlib import Path
import webbrowser
from difflib import SequenceMatcher as SM

from flox import Flox, ICON_SETTINGS

import requests
import helper as h
from helper import ConnectionTimeout
from json.decoder import JSONDecodeError

def download_icons(url):
    """
    Downloads the icons for all guilds and saves them to the temp directory
    """

    icon_name = url.split('/')[-1]
    icon_path = Path(gettempdir(), icon_name)
    if not icon_path.exists():
        r = requests.get(url, stream=True)
        with open(icon_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    return str(icon_path)

def match(query, match):
    return int(SM(lambda x: x==" " or x=="-" or x=="_", query.lower(), match.lower()).ratio() * 100)

class DiscordQuickswitcher(Flox):

    def query(self, query):
        token = self.settings['api_key']
        try:
            guilds = h.get_guilds(token)
            for guild in guilds:
                for channel in guild.get_channels():
                    channel_match = match(query, f'{guild.name} {channel.category()} {channel.name}')
                    icon = download_icons(channel.icon_url())
                    self.add_item(
                        title=f"#{channel.name}",
                        subtitle=f"{guild.name} - {channel.category()}".replace(' - None', ''),
                        icon=icon,
                        method=self.open_in_desktop,
                        parameters=[channel.uri()],
                        score=channel_match
                    )
        except (ConnectionTimeout, JSONDecodeError):
            self.add_item(
                title="Could not connect to Discord",
                subtitle="Please check your settings and connection...",
                icon=ICON_SETTINGS,
                method=self.open_setting_dialog
            )

    def context_menu(self, data):
        pass

    def open_in_desktop(self, uri):
        webbrowser.open(uri)

if __name__ == "__main__":
    DiscordQuickswitcher()
