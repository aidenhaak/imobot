
from . import plugin

class Stats(plugin.Plugin):
    def __init__(self, url):
        super().__init__()
        self.url = url

    @plugin.command("stats")
    def stats(self, message):
        return f"Stats: {self.url}"