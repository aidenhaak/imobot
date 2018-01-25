
from cerberus import Validator
import yaml

import irc

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
                            "type" : "dict",
                            "schema" : 
                            {
                                "name" : { "type" : "string", "required" : True, },
                                "kwargs" :
                                {
                                    "type" : "dict",
                                    "keyschema" : { "type" : "string" }
                                }
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
                self.channels = [irc.Channel(channel["name"]) for channel in settings["channels"]]
            else:
                raise BotSettingsError(validator.errors)


class BotSettingsError(Exception):
    def __init__(self, errors):
        self.errors = errors

class BotSettingsValidator(Validator):

    def __init__(self):
        super().__init__(BOT_SETTINGS_SCHEMA)