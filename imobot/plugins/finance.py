
import datetime
import json

from twisted.words.protocols.irc import assembleFormattedText, attributes
import lxml.html
from urllib.request import urlopen

from . import plugin

class AsxStockQuotes(plugin.Plugin):
    cached_asx_data = {}

    @plugin.command("asx")
    def asx_stock_quote(self, message):    
        _, _, asx_code = message.message.lstrip("!").partition(" ")

        cached_data = self.cached_asx_data.get(asx_code, None)
        if cached_data is None or self.is_asx_data_stale(cached_data[0]):
            cached_data = self.get_asx_data(asx_code)

        return f"Unabled to get ASX data for {asx_code}" if cached_data is None else cached_data[1]

    def is_asx_data_stale(self, asx_data_cache_time):
        if asx_data_cache_time is None:
            return True

        delta = datetime.datetime.now() - asx_data_cache_time
        return delta.seconds > 120

    def get_asx_data(self, asx_code):
        try:
            response = urlopen(f"https://au.finance.yahoo.com/quote/{asx_code}.AX")
            html = response.read().decode("utf8")
            root = lxml.html.fromstring(html)
            company_name = root.xpath("//h1[@data-reactid=\"7\"]")[0].text[9:]

            response = urlopen(f"https://query1.finance.yahoo.com/v8/finance/chart/{asx_code}.AX?range=2d&interval=1d&indicators=quote&includeTimestamps=true")
            data = json.loads(response.read().decode("utf8"))

            close_data = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
            previous_close = close_data[0]
            current_price = close_data[1]

            change = current_price - previous_close
            percent_change = change / previous_close * 100
         
            formatted_text = self.get_formatted_text(company_name, asx_code.upper(), current_price, change, percent_change)
            asx_data = (datetime.datetime.now(), formatted_text)
            self.cached_asx_data[asx_code] = asx_data
            return asx_data
        except Exception:
            pass # Ignore - just means ASX data doesn't get updated.

    def get_formatted_text(self, company_name, asx_code, current_price, change, percent_change):
        if percent_change == 0:
            return assembleFormattedText(
                attributes.normal[
                    f"{company_name} (ASX:{asx_code}) ${current_price:,.2f} ",
                    attributes.fg.gray[f"► $0 (0%)"]           
                ])        
        elif percent_change < 0:
            return assembleFormattedText(
                attributes.normal[
                    f"{company_name} (ASX:{asx_code}) ${current_price:,.2f} ",
                    attributes.fg.red[f"▼ ${abs(change):.2f} ({abs(percent_change):.2f}%)"]           
                ])
        else:
            return assembleFormattedText(
                attributes.normal[
                    f"{company_name} (ASX:{asx_code}) ${current_price:,.2f} ",
                    attributes.fg.green[f"▲ ${abs(change):.2f} ({abs(percent_change):.2f}%)"]           
                ])

