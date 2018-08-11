
import os
import re

from errbot import BotPlugin, re_botcmd
from urllib.request import urlopen

import lxml.html

URL_REGEX = r"(?u)(https?://\S+)"

class UrlTitles(BotPlugin):
    @re_botcmd(pattern = URL_REGEX, prefixed = False, flags = re.IGNORECASE)
    def title_unfurl(self, message, match):
        url = match[0]
        html = urlopen(match[0])
        tree = lxml.html.parse(html)
        title = tree.find(".//title")
        return title.text if title else None
