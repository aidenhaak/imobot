
import sys, os
sys.path.append(os.path.dirname(__file__))

import plugin

class Stats(plugin.Plugin):
    @plugin.command("stats")
    def stats(self, message):
        return "Stats: http://stats.example.com/"