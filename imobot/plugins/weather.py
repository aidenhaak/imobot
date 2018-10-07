
import datetime

import fake_useragent
import lxml.html
from errbot import BotPlugin, botcmd, arg_botcmd
import urllib.request 

class Weather(BotPlugin):

    BOM_URL = "http://www.bom.gov.au/"

    USER_AGENT_FALLBACK = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"

    weather_data_cache_time = None

    cached_weather_data = {}

    location_names = {
        "sydney" : "Sydney",
        "syd" : "Sydney",
        "melbourne" : "Melbourne",
        "mel" : "Melbourne",
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

    @botcmd(name="w", split_args_with=None)
    def weather_command1(self, message, args):
        """Gets the weather for one or more locations."""
        yield from self.weather_command_aux(message, args)

    @botcmd(name="weather", split_args_with=None)
    def weather_command2(self, message, args):
        """Gets the weather for one or more locations."""
        yield from self.weather_command_aux(message, args)

    def weather_command_aux(self, message, args):
        if not args:
            yield "I'm sorry, I couldn't parse the arguments; the following arguments are required: locations"
            yield "usage: weather [locations]"
            return

        for arg in args:
            yield self.get_weather_message(arg)

    def get_weather_message(self, location = None):
        location_name = self.location_names.get(location.lower(), None)
        if location_name is not None:
            if self.is_weather_data_stale():
                self.update_cached_weather_data()

            return self.cached_weather_data[location_name]
        else:
            return f"Unkown location: {location}"

    def is_weather_data_stale(self):
        if self.weather_data_cache_time is None:
            return True

        delta = datetime.datetime.now() - self.weather_data_cache_time
        return delta.seconds > 120

    def update_cached_weather_data(self):
        try:
            request = urllib.request.Request(
                self.BOM_URL, 
                data = None, 
                headers = { 
                    "User-Agent": fake_useragent.UserAgent(fallback = self.USER_AGENT_FALLBACK).random
                }
            )
            html = urllib.request.urlopen(request)
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
                temp_min = minmax_element.text.strip() if minmax_element.text else None
                temp_max = minmax_element.xpath("span[@class=\"max\"]")[0].text.strip()
                
                summary_element = tip_element.xpath("p[@class=\"precis\"]")[0]
                summary = summary_element.text.strip()

                if temp_min:
                    weather_data[location] = f"{location} Now: {temp_now}C {wind} Tomorrow: {temp_min}C/{temp_max}C {summary}"
                else:
                    weather_data[location] = f"{location} Now: {temp_now}C {wind} Today: {temp_max}C {summary}"                

            # All the locations weather data was retrieved successfully. Update the cache time and data. 
            self.weather_data_cache_time = datetime.datetime.now()
            self.cached_weather_data = weather_data
        except Exception as e:
            pass # Ignore - just means cached weather data doesn't get updated.