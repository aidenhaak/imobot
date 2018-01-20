
import os
import re

from urllib.request import urlopen

import lxml.html

import plugin

URL_REGEX = r"(?u)(https?://\S+)"

class UrlTitles(plugin.Plugin):
    @plugin.rule(URL_REGEX)
    def title_auto(self, message):
        urls = re.compile(URL_REGEX).findall(message.message)
        titles = []
        for url in urls:
            html = urlopen(url)
            tree = lxml.html.parse(html)
            titles.append(tree.find(".//title").text)

        return os.linesep.join(titles)
