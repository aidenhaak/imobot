
import os
import sys
import logging
import threading

from twisted.internet import defer, endpoints, task
from twisted.python import log
from twisted.application import internet

import bot
import conf

def main(reactor, description):
    endpoint = endpoints.clientFromString(reactor, description)
    factory = bot.IrcBotFactory()
    d = endpoint.connect(factory)
    d.addCallback(lambda protocol: protocol.deferred)
    return d

if __name__ == "__main__":
    log.startLogging(sys.stderr)
    task.react(main, ["tcp:{}:{}".format(conf.HOSTNAME, conf.PORT)])
