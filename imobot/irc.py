
class Message(object):
    """
    Represents a message sent over IRC.
    """
    def __init__(self, user, channel, message, is_action):
        self.user = user
        self.nickname = user.split("!", 1)[0]
        self.channel = channel
        self.message = message
        self.is_action = is_action
    
    def __str__(self):
        return self.message


class Channel(object):
    def __init__(self, name):
        self.name = name