
import yaml

from cerberus import Validator

import irc
from plugins import plugin

BOT_SETTINGS_SCHEMA = {
        "nickname" : { "type" : "string", "required" : True },
        "password" : { "type" : "string", "required" : True },
        "hostname" : { "type" : "string", "required" : True },
        "port": { "type": "integer", "min" : 1, "max" : 65536, "required" : True },
        "channels" : 
        {
            "required" : True,
            "type" : "list",
            "schema" : 
            {
                "type" : "dict",
                "schema" : 
                {
                    "name" : { "type" : "string", "required" : True },
                    "plugins" :
                    {
                        "required" : True,
                        "type" : "list",
                        "schema" : 
                        {
                            "allow_unknown" : True,
                            "type" : "dict",
                            "schema" : 
                            {
                                "name" : { "type" : "string", "required" : True, }
                            }
                        }
                    }
                }
            }
        }
    }

class BotSettings(object):
    def __init__(self, settings_filepath):
        with open(settings_filepath, 'r') as stream:
            settings = yaml.load(stream)
            validator = Validator(BOT_SETTINGS_SCHEMA)

            if validator.validate(settings):            
                self.nickname = settings["nickname"]
                self.password = settings["password"]
                self.hostname = settings["hostname"]
                self.port = settings["port"]
                self._load_channels(settings["channels"])
            else:
                raise BotSettingsError(validator.errors)

    def _load_channels(self, channels):
        self.channels = []

        for settings in channels:
            channel_plugins = self._load_channel_plugins(settings["plugins"])
            self.channels.append(irc.Channel(settings["name"], channel_plugins))

    def _load_channel_plugins(self, plugin_settings):
        channel_plugins = []

        for settings in plugin_settings:
            plugin_name = settings.pop("name")
            channel_plugin = plugin.load_plugin(plugin_name, **settings)
            if channel_plugin is not None:
                channel_plugins.append(channel_plugin)

        return channel_plugins

class BotSettingsError(Exception):
    def __init__(self, errors):
        self.errors = errors
