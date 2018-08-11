
import datetime
import json

import lxml.html
from errbot import BotPlugin, arg_botcmd
from urllib.request import urlopen

class Finance(BotPlugin):
    cached_asx_data = {}

    ASX_URL = "https://au.finance.yahoo.com/quote/{asx_code}.AX"

    ASX_QUERY_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{asx_code}.AX?range=1d&interval=1d"

    @arg_botcmd("asx_code", type = str)
    def asx(self, message, asx_code = None):    
        if asx_code:
            cached_data = self.cached_asx_data.get(asx_code, None)
            if cached_data is None or self.is_asx_data_stale(cached_data[0]):
                cached_data = self.get_asx_data(asx_code)

        return f"Unable to get ASX data for {asx_code}" if cached_data is None else cached_data[1]

    def is_asx_data_stale(self, asx_data_cache_time):
        if asx_data_cache_time is None:
            return True

        delta = datetime.datetime.now() - asx_data_cache_time
        return delta.seconds > 120

    def get_asx_data(self, asx_code):
        try:
            response = urlopen(self.ASX_URL.format(asx_code = asx_code))
            html = response.read().decode("utf8")
            root = lxml.html.fromstring(html)
            company_name = root.xpath("//h1[@data-reactid=\"7\"]")[0].text[9:]

            response = urlopen(self.ASX_QUERY_URL.format(asx_code = asx_code))
            data = json.loads(response.read().decode("utf8"))

            previous_close = data["chart"]["result"][0]["meta"]["chartPreviousClose"]
            current_price = data["chart"]["result"][0]["indicators"]["quote"][0]["close"][0]

            change = current_price - previous_close
            percent_change = change / previous_close * 100
            
            asx_quote = self.get_asx_quote(company_name, asx_code.upper(), current_price, change, percent_change)
            asx_data = (datetime.datetime.now(), asx_quote)
            self.cached_asx_data[asx_code] = asx_data
            return asx_data
        except Exception:
            pass # Ignore - just means ASX data doesn't get updated.

    def get_asx_quote(self, company_name, asx_code, current_price, change, percent_change):
        grey = "{:color='grey'}"
        green = "{:color='green'}"
        red = "{:color='red'}"

        if percent_change == 0:
            return f"{company_name} (ASX:{asx_code}) ${current_price:,.2f} `► $0 (0%)`{grey}" 
        elif percent_change < 0:
            return f"{company_name} (ASX:{asx_code}) ${current_price:,.2f} `▼ ${abs(change):.2f} ({abs(percent_change):.2f}%)`{red}"
        else:
            return f"{company_name} (ASX:{asx_code}) ${current_price:,.2f} `▲ ${abs(change):.2f} ({abs(percent_change):.2f}%)`{green}"

    XE_URL = "http://www.xe.com/currencyconverter/convert/?Amount=1&From={currency_from}&To={currency_to}"

    cached_fx_data = {}

    @arg_botcmd("currency_from", type = str)
    @arg_botcmd("currency_to", type = str)
    @arg_botcmd("--amount", type = float, default = 1.0)
    def fx(self, message, currency_from = None, currency_to = None, amount = None):
        cached_data_key = self.get_cache_data_key(currency_from, currency_to)
        fx_data = self.cached_fx_data.get(cached_data_key, None)
        if fx_data is None or self.is_fx_data_stale(fx_data[0]):
            fx_data = self.get_fx_data(currency_from, currency_to)
            self.cached_fx_data[cached_data_key] = fx_data

        if fx_data is None:
            return f"Unable to get FX data for {currency_from} to {currency_to}"
        else:
            return self.get_fx_quote_message(currency_from, currency_to, amount, fx_data[1])

    def get_cache_data_key(self, currency_from, currency_to):
        return currency_from + currency_to

    def get_fx_quote_message(self, currency_from, currency_to, amount, conversion_rate):
        converted_amount = amount * conversion_rate
        return f"{amount} {currency_from.upper()} = {converted_amount} {currency_to.upper()}"

    def is_fx_data_stale(self, fx_data_cache_time):
        if fx_data_cache_time is None:
            return True

        delta = datetime.datetime.now() - fx_data_cache_time
        return delta.seconds > 120

    def get_fx_data(self, currency_from, currency_to):
        try:
            url = self.XE_URL.format(currency_from = currency_from, currency_to = currency_to)
            response = urlopen(url)
            html = response.read().decode("utf8")

            root = lxml.html.fromstring(html)
            container = root.xpath("//div[@id=\"ucc-container\"]")[0]
            amount_wrap_element = container.xpath("//span[@class=\"uccAmountWrap\"]")[0]
            to_amount_element = amount_wrap_element.xpath("//span[@class=\"uccResultAmount\"]")[0]

            return (datetime.datetime.now(), float(to_amount_element.text))
        except Exception:
            pass # Ignore - just means FX data doesn't get updated.
