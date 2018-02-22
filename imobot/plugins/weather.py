
import datetime
from twisted.words.protocols.irc import assembleFormattedText, attributes
import lxml.html
from urllib.request import urlopen

from . import plugin

BOM_URL = "http://www.bom.gov.au/"

class Weather(plugin.Plugin):

    weather_data_cache_time = None

    cached_weather_data = {}

    location_names = {
        "sydney" : "Sydney",
        "syd" : "Sydney",
        "melbourne" : "Melbourne",
        "mlb" : "Melbourne",
        "brisbane" : "Brisbane",
        "bne" : "Brisbane",
        "perth" : "Perth",
        "per" : "Perth",
        "adelaide" : "Adelaide",
        "ade" : "Adelaide",
        "hobart" : "Hobart",
        "hob" : "Hobart",
        "canberra" : "Canberra",
        "can" : "Canberra",
        "darwin" : "Darwin",
        "dar" : "Darwin"
    }

    @plugin.command("w", "weather")
    def weather(self, message):    
        _, _, location = message.message.lstrip("!").partition(" ")
        location_name = self.location_names.get(location.lower(), None)
        if location_name is not None:
            if self.is_weather_data_stale():
                self.update_cached_weather_data()
            return self.cached_weather_data[location_name]
        else:
            return f"Unkown location: {location_name}"

    def is_weather_data_stale(self):
        if self.weather_data_cache_time is None:
            return True

        delta = datetime.datetime.now() - self.weather_data_cache_time
        return delta.seconds > 120

    def update_cached_weather_data(self):
        try:
            html = urlopen(BOM_URL)
            tree = lxml.html.parse(html)

            weather_data = {}

            today_element = tree.xpath("//section[@id=\"today\"]")[0]
            capitals_element = today_element.xpath("//div[@class=\"capitals clearfix\"]")[0]

            for child in capitals_element:
                tip_element = child.xpath("a[@class=\"tip\"]")[0]
                location_element = tip_element.xpath("h3")[0]
                location = location_element.text.strip()
                
                temp_now_element = tip_element.xpath("p[@class=\"now\"]")[0]
                temp_now = list(temp_now_element)[0].text
                
                wind_element = tip_element.xpath("p[@class=\"wind\"]")[0]
                wind = wind_element.text.strip()
                
                minmax_element = tip_element.xpath("p[@class=\"minmax\"]")[0]
                temp_min = minmax_element.text.strip()
                temp_max = minmax_element[0].text.strip()
                
                summary_element = tip_element.xpath("p[@class=\"precis\"]")[0]
                summary = summary_element.text.strip()

                if temp_min:
                    weather_data[location] = assembleFormattedText(
                        attributes.normal[attributes.bold[location],
                        f" Now: {temp_now}C {wind} Tomorrow: {temp_min}C/{temp_max}C {summary}"])
                else:
                    weather_data[location] = assembleFormattedText(
                        attributes.normal[attributes.bold[location],
                        f" Now: {temp_now}C {wind} Today: {temp_max}C {summary}"])
                

            # All the locations weather data was retrieved successfully. Update the cache time and data. 
            self.weather_data_cache_time = datetime.datetime.now()
            self.cached_weather_data = weather_data
        except:
            pass # Ignore - just means cached weather data doesn't get updated.