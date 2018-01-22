
import argparse
import sys

from twisted.internet import defer, endpoints, task
from twisted.python import log
from twisted.application import internet

import bot
import settings

def main(reactor, bot_settings):
    description = "tcp:{}:{}".format(bot_settings.hostname, bot_settings.port)
    endpoint = endpoints.clientFromString(reactor, description)
    factory = bot.IrcBotFactory(bot_settings)
    d = endpoint.connect(factory)
    d.addCallback(lambda protocol: protocol.deferred)
    return d

def parse_bot_settings():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("settings", metavar="bot-settings-file", type=str, help="the bot settings file")

    args = parser.parse_args()
    return settings.BotSettings(args.settings)

if __name__ == "__main__":
    bot_settings = parse_bot_settings()
    log.startLogging(sys.stderr)
    task.react(main, [bot_settings])
