
import datetime
from twisted.words.protocols.irc import assembleFormattedText, attributes
import lxml.html
from urllib.request import urlopen

from . import plugin

CMC_URL = "https://coinmarketcap.com/"

class Crypto(plugin.Plugin):
    crypto_data_cache_time = None

    cached_crypto_data = {}

    crypto_names = {
        "bitcoin" : "Bitcoin",
        "btc" : "Bitcoin",
        "ethereum" : "Ethereum",
        "eth" : "Ethereum",
        "ripple" : "Ripple",
        "xrp" : "Ripple",
        "bitcoin cash" : "Bitcoin Cash",
        "bch" : "Bitcoin Cash",
        "litecoin" : "Litecoin ",
        "ltc" : "Litecoin",
        "bitcoin gold" : "Bitcoin Gold",
        "btg" : "Bitcoin Gold",
    }

    @plugin.command("c", "crypto")
    def weather(self, message):    
        _, _, crypto = message.message.lstrip("!").partition(" ")
        crypto_name = self.crypto_names.get(crypto, None)
        if crypto_name is not None:
            if self.is_crypto_data_stale():
                self.update_cached_crypto_data()

            return self.cached_crypto_data[crypto_name]
        else:
            return f"Unkown cryptocurrency: {crypto_name}"

    def is_crypto_data_stale(self):
        if self.crypto_data_cache_time is None:
            return True

        delta = datetime.datetime.now() - self.crypto_data_cache_time
        return delta.seconds > 120

    def update_cached_crypto_data(self):
        try:
            html = urlopen(CMC_URL)
            tree = lxml.html.parse(html)

            crypto_data = {}

            self.add_crypto_data(crypto_data, tree, "Bitcoin", "BTC")
            self.add_crypto_data(crypto_data, tree, "Ethereum", "ETH")
            self.add_crypto_data(crypto_data, tree, "Ripple", "XRP")
            self.add_crypto_data(crypto_data, tree, "Bitcoin Cash", "BCH")
            self.add_crypto_data(crypto_data, tree, "Litecoin", "LTC")
            self.add_crypto_data(crypto_data, tree, "Bitcoin Gold", "BTG")

            # All the crypto data was retrieved successfully. Update the cache time and data. 
            self.crypto_data_cache_time = datetime.datetime.now()
            self.cached_crypto_data = crypto_data
        except:
            pass # Ignore - just means crypto data doesn't get updated.

    def add_crypto_data(self, crypto_data, tree, crypto_name, crypto_symbol):
        crypto_data[crypto_name] = self.get_crypto_data(tree, crypto_name, crypto_symbol)

    def get_crypto_data(self, tree, crypto_name, crypto_symbol):
        crypto_id = crypto_name.lower().replace(' ', '-')
        crypto_element = tree.xpath(f"//tr[@id=\"id-{crypto_id}\"]")[0]
        crypto_element_children = list(crypto_element)

        price_element = crypto_element_children[3]
        price = float(price_element[0].text.strip()[1:])
        change_element = crypto_element_children[6]
        percent_change = float(change_element.text.strip()[:-1])
        absolute_change = percent_change * price / 100

        if percent_change == 0:
            return assembleFormattedText(
                attributes.normal[attributes.bold[crypto_name],
                f" ({crypto_symbol}) ${price:,.2f} (USD) ",
                attributes.fg.gray[f"► $0 (0%)"]           
                ])        
        elif percent_change < 0:
            return assembleFormattedText(
                attributes.normal[attributes.bold[crypto_name],
                f" ({crypto_symbol}) ${price:,.2f} (USD) ",
                attributes.fg.red[f"▼ ${abs(absolute_change):.2f} ({abs(percent_change):.2f}%)"]           
                ])
        else:
            return assembleFormattedText(
                attributes.normal[attributes.bold[crypto_name],
                f" ({crypto_symbol}) ${price:,.2f} (USD) ",
                attributes.fg.green[f"▲ ${abs(absolute_change):.2f} ({abs(percent_change):.2f}%)"]           
                ])