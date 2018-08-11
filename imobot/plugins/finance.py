
import datetime
import json

import lxml.html
from errbot import BotPlugin, arg_botcmd
from urllib.request import urlopen

class Finance(BotPlugin):
    cached_stock_data = {}

    YAHOO_FINANCE_URL = "https://au.finance.yahoo.com/quote/{stock_code}"

    YAHOO_FINANCE_QUERY_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{stock_code}?range=1d&interval=1d"

    @arg_botcmd("stock_code", type = str)
    def ndq(self, message, stock_code = None):  
        return self.get_stock_quote(stock_code)

    @arg_botcmd("stock_code", type = str)
    def nyse(self, message, stock_code = None):
        return self.get_stock_quote(stock_code)

    @arg_botcmd("stock_code", type = str)
    def asx(self, message, stock_code = None):    
        asx_code = self.to_asx_code(stock_code)
        return self.get_stock_quote(asx_code)

    def get_stock_quote(self, stock_code):
        stock_data = None

        if stock_code:
            stock_data = self.cached_stock_data.get(stock_code, None)
            if stock_data is None or self.is_stock_data_stale(stock_data[0]):
                stock_data = self.get_stock_data(stock_code)

        return f"Unable to get stock data for {stock_code}" if stock_data is None else stock_data[1]


    def to_asx_code(self, stock_code):
        return f"{stock_code}.AX"

    def is_stock_data_stale(self, stock_data_cache_time):
        if stock_data_cache_time is None:
            return True

        delta = datetime.datetime.now() - stock_data_cache_time
        return delta.seconds > 120

    def get_stock_data(self, stock_code):
        try:
            response = urlopen(self.YAHOO_FINANCE_URL.format(stock_code = stock_code))
            html = response.read().decode("utf8")
            root = lxml.html.fromstring(html)
            company_name = root.xpath("//h1[@data-reactid=\"7\"]")[0].text
            company_name = company_name[company_name.find("-") + 2:]

            response = urlopen(self.YAHOO_FINANCE_QUERY_URL.format(stock_code = stock_code))
            data = json.loads(response.read().decode("utf8"))

            previous_close = round(data["chart"]["result"][0]["meta"]["chartPreviousClose"], 4)
            current_price = round(data["chart"]["result"][0]["indicators"]["quote"][0]["close"][0], 4)

            change = current_price - previous_close
            percent_change = change / previous_close * 100
            
            stock_quote = self.get_formatted_stock_quote(company_name, stock_code.upper(), current_price, change, percent_change)
            stock_data = (datetime.datetime.now(), stock_quote)
            self.cached_stock_data[stock_code] = stock_data
            return stock_data
        except Exception:
            pass # Ignore - just means stock data doesn't get updated.

    def get_formatted_stock_quote(self, company_name, stock_code, current_price, change, percent_change):
        grey = "{:color='grey'}"
        green = "{:color='green'}"
        red = "{:color='red'}"

        change_in_dollars = abs(change)
        change_in_cents = 100 * change_in_dollars
        change = f"${change_in_dollars:,.2f}" if current_price > 1 else f"{change_in_cents:,.2f}¢"

        current_price_in_dollars = current_price
        current_price_in_cents = 100 * current_price_in_dollars
        current_price = f"${current_price:,.2f}" if current_price > 1 else f"{current_price_in_cents:,.2f}¢"

        if percent_change == 0:
            return f"{company_name} ({stock_code}) {current_price} `► $0 (0%)`{grey}" 
        elif percent_change < 0:
            return f"{company_name} ({stock_code}) {current_price} `▼ {change} ({abs(percent_change):.2f}%)`{red}"
        else:
            return f"{company_name} ({stock_code}) {current_price} `▲ {change} ({abs(percent_change):.2f}%)`{green}"

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
