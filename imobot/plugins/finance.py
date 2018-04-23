
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

        return f"Unable to get ASX data for {asx_code}" if cached_data is None else cached_data[1]

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

            response = urlopen(f"https://query1.finance.yahoo.com/v8/finance/chart/{asx_code}.AX?range=1d&interval=1d")
            data = json.loads(response.read().decode("utf8"))

            previous_close = data["chart"]["result"][0]["meta"]["chartPreviousClose"]
            current_price = data["chart"]["result"][0]["indicators"]["quote"][0]["close"][0]

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

class FxQuotes(plugin.Plugin):
    XE_URL = "http://www.xe.com/currencyconverter/convert/?Amount=1&From={currency_from}&To={currency_to}"

    cached_fx_data = {}

    @plugin.command("fx")
    def fx_quote(self, message):
        args = message.message.lstrip("!").partition(" ")[2].split(" ")

        if len(args) != 2 and len(args) != 3:
            return "Usage: !fx <currency-from> <currency-to> [amount]"
        elif len(args) == 3 and not self.is_float(args[2]):
            return "Usage: !fx <currency-from> <currency-to> [amount] - amount must be number"

        currency_from = args[0].lower()
        currency_to = args[1].lower()
        amount = float(args[2]) if len(args) == 3 else 1

        cached_data_key = self.get_cache_data_key(currency_from, currency_to)
        fx_data = self.cached_fx_data.get(cached_data_key, None)
        if fx_data is None or self.is_fx_data_stale(fx_data[0]):
            fx_data = self.get_fx_data(currency_from, currency_to)
            self.cached_fx_data[cached_data_key] = fx_data

        if fx_data is None:
            return f"Unable to get FX data for {currency_from} to {currency_to}"
        else:
            return self.get_fx_quote_message(currency_from, currency_to, amount, fx_data[1])

    def is_float(self, value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def get_cache_data_key(self, currency_from, currency_to):
        return currency_from + currency_to

    def get_fx_quote_message(self, currency_from, currency_to, amount, conversion_rate):
        converted_amount = amount * conversion_rate
        return f"{amount} {currency_from.upper()} = {converted_amount} {currency_to.upper()}"

    def get_formatted_text(self, currency_from, currency_to, amount, cached_data):
        return f"{amount}{currency_from} {amount * cached_data[1]} {currency_to}"

    def is_fx_data_stale(self, fx_data_cache_time):
        if fx_data_cache_time is None:
            return True

        delta = datetime.datetime.now() - fx_data_cache_time
        return delta.seconds > 120

    def get_fx_data(self, currency_from, currency_to):
        try:
            url = self.XE_URL.format(currency_from=currency_from, currency_to=currency_to)
            response = urlopen(url)
            html = response.read().decode("utf8")

            root = lxml.html.fromstring(html)
            container = root.xpath("//div[@id=\"ucc-container\"]")[0]
            amount_wrap_element = container.xpath("//span[@class=\"uccAmountWrap\"]")[0]
            to_amount_element = amount_wrap_element.xpath("//span[@class=\"uccResultAmount\"]")[0]

            return (datetime.datetime.now(), float(to_amount_element.text))
        except Exception as e:
            pass # Ignore - just means FX data doesn't get updated.
