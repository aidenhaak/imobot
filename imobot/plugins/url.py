
import os
import re
import urllib.request 

from errbot import BotPlugin, re_botcmd
import fake_useragent
import lxml.html

URL_REGEX = r"(?u)(https?://\S+)"

USER_AGENT_FALLBACK = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"

class UrlTitles(BotPlugin):
    @re_botcmd(pattern = URL_REGEX, prefixed = False, flags = re.IGNORECASE)
    def title_unfurl(self, message, match):
        url = match[0]
        request = urllib.request.Request(
                url, 
                data=None, 
                headers={
                    "User-Agent": fake_useragent.UserAgent(fallback = USER_AGENT_FALLBACK).random
                }
            )
        html = urllib.request.urlopen(request)
        tree = lxml.html.parse(html)
        title = tree.find(".//title")
        return title.text if title is not None else None
