
import twisted.words.protocols.irc as twisted_irc
from twisted.internet import defer, protocol, reactor

import irc
from plugins import eightball, stats, url

class IrcProtocol(twisted_irc.IRCClient):

    def __init__(self, bot_settings):
        self.channels = bot_settings.channels
        self.nickname = bot_settings.nickname
        self.password = bot_settings.password
        self.deferred = defer.Deferred()

    def signedOn(self):
        for channel in self.channels:
            self.join(channel.name)

    def privmsg(self, user, channel_name, message):
        channel = next((channel for channel in self.channels if channel.name == channel_name), None)
        self.dispatch_message(irc.Message(user, channel, message, False))
    
    def action(self, user, channel_name, message):
        channel = next((channel for channel in self.channels if channel.name == channel_name), None)
        self.dispatch_message(irc.Message(user, channel, message, True))
    
    def dispatch_message(self, message):
        for plugin in message.channel.plugins:
            plugin.process_message(self, message)


class IrcBotFactory(protocol.ReconnectingClientFactory):

    protocol = IrcProtocol

    def __init__(self, bot_settings):
        self.bot_settings = bot_settings

    def buildProtocol(self, addr):
        p = self.protocol(self.bot_settings)
        p.factory = self
        return p