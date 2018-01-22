
import yaml

import irc

class BotSettings(object):
    def __init__(self, settings_filepath):
        with open(settings_filepath, 'r') as stream:
            settings = yaml.load(stream)
            
            self.nickname = settings["nickname"]
            self.password = settings["password"]
            self.hostname = settings["hostname"]
            self.port = settings["port"]

            print([channel["name"] for channel in settings["channels"]])
            self.channels = [irc.Channel(channel["name"]) for channel in settings["channels"]]
