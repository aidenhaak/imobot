
from twisted.words.protocols import irc
from twisted.internet import defer, protocol, reactor

import conf
from message import Message
import plugins.stats
import plugins.url

class IrcProtocol(irc.IRCClient):

    def __init__(self):
        self.channels = conf.CHANNELS
        self.nickname = conf.NICKNAME
        self.password = conf.PASSWORD
        self.plugins = [plugins.stats.Stats(), plugins.url.UrlTitles()]

        self.deferred = defer.Deferred()

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
    
    def signedOn(self):
        for channel in self.channels:
            self.join(channel)

    def privmsg(self, user, channel, message):
        self.dispatch_message(Message(user, channel, message, False))
    
    def action(self, user, channel, message):
        self.dispatch_message(Message(user, channel, message, True))
    
    def dispatch_message(self, message):
        for plugin in self.plugins:
            plugin.process_message(self, message)


class IrcBotFactory(protocol.ReconnectingClientFactory):

    protocol = IrcProtocol