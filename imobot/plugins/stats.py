
from errbot import BotPlugin, botcmd

class Stats(BotPlugin):
    @botcmd
    def stats(self, message, args):
        stats_urls = getattr(self.bot_config, 'STATS_URLS', None)
        if stats_urls is None:
            return 'No stats URL defined.'

        room_name = message.frm.room.room   
        stats_url = stats_urls.get(room_name, None)
        if stats_url:
            return f"Stats: {stats_url}"