
import re

from twisted.internet import defer

def command(*command_list):
    def decorator(function):
        if not hasattr(function, "commands"):
            function.commands = []
        function.commands.extend(command_list)
        return function

    return decorator

def rule(value):
    def decorator(function):
        if not hasattr(function, "rules"):
            function.rules = []
        function.rules.append(value)
        return function

    return decorator

class Plugin(object):
    def __init__(self):
        self.commands = {}
        self.rules = []
        
        methods = [getattr(self, method) for method in dir(self) if callable(getattr(self, method))]
        for method in methods:
            if hasattr(method, "commands"):
                for x in method.commands:
                    self.commands[x] = method

            if hasattr(method, "rules"):
                for rule in method.rules:
                    self.rules.append((re.compile(rule), method))

    def process_message(self, protocol, message):
        command_name, _, _ = message.message.lstrip("!").partition(" ")
        command = self.commands.get(command_name, None)
        if command is not None:
            d = defer.maybeDeferred(command, message)
            d.addErrback(self._error)
            d.addCallback(self._msg, message.channel, protocol)
        else:
            for regex, method in self.rules:
                if regex.search(message.message):
                    d = defer.maybeDeferred(method, message)
                    d.addErrback(self._error)
                    d.addCallback(self._msg, message.channel, protocol)

    def _error(self, failure):
        return failure.getErrorMessage()

    def _msg(self, message, user, protocol):
        protocol.msg(user, message)

