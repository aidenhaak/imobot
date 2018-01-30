
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
            d.addCallback(self._msg, message.channel.name, protocol)
        else:
            for regex, method in self.rules:
                if regex.search(message.message):
                    d = defer.maybeDeferred(method, message)
                    d.addErrback(self._error)
                    d.addCallback(self._msg, message.channel.name, protocol)

    def _error(self, failure):
        return failure.getErrorMessage()

    def _msg(self, message, user, protocol):
        protocol.msg(user, message)

def load_plugin(plugin_name, **kwargs):
    class_type = next((cls_ for cls_ in type.__subclasses__(Plugin) if cls_.__name__ == plugin_name), None)
    if class_type is not None and isinstance(class_type, type):
        return class_type(**kwargs)
    else:
        return None      
