
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
        if self._is_command(message.message):
            command_name, _, args = message.message.lstrip("!").partition(" ")
            command = self.commands.get(command_name, None)
            if command is not None:
                # todo should really pass the message object to the command func
                d = defer.maybeDeferred(command, args)
                d.addErrback(self._error)
                d.addCallback(self._msg, message.channel, protocol)
        else:
            for regex, method in self.rules:
                if regex.search(message.message):
                    # todo should really pass the message object to the rule func
                    d = defer.maybeDeferred(method, message.message)
                    d.addErrback(self._error)
                    d.addCallback(self._msg, message.channel, protocol)

    def _error(self, failure):
        return failure.getErrorMessage()

    def _is_command(self, message):
        return message.startswith("!")

    def _msg(self, message, user, protocol):
        protocol.msg(user, message)

