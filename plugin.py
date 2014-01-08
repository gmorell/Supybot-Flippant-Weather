###
# Copyright (c) 2014, Gabriel Morell-Pacheco
# All rights reserved.
#
#
###
import requests
import json
import datetime
import pytz

from random import choice
import os

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircmsgs as ircmsgs
import supybot.conf as conf

from secrets import WUNDERKEY
lookup_str = "http://api.wunderground.com/api/%s/conditions/forecast/q/IA/" % WUNDERKEY # add "%s.json" to the end
#lookup_str = "http://api.wunderground.com/api/%s/geolookup/forecast/q/IA/" % WUNDERKEY # add "%s.json" to the end

CACHE_PERIOD = 600 # seconds = 10min
    
        
class Weather2014(callbacks.Plugin):
    """Add the help for "@plugin help Weather2014" here
    This should describe *how* to use this plugin."""
    threaded = True
    def __init__(self,irc):
        self.__parent = super(Weather2014, self)
        self.__parent.__init__(irc)
        self.pastweatherlookups = {}
        self.pastforecastlookups = {}
        
    def weather_lookup(self,lookup):
        final_lookup = lookup_str + lookup + ".json"
        
        r = requests.get(final_lookup)
        j = json.loads(r.text)
        if 'current_observation' in j.keys():
            return j,True
        else:
            e = j['response']['error']['description']
            return e,False
        
    def weather_formatting(self,json):
        output = 'Current Conditions for %s, %s: [%s] [%s] [wind: %s] [%s : %s] [%s : %s]' % (
        json['current_observation']['observation_location']['full'],
        json['current_observation']['observation_location']['country'],
        json['current_observation']['weather'],
        json['current_observation']['temperature_string'],
        json['current_observation']['wind_string'],
        json['forecast']['txt_forecast']['forecastday'][0]['title'],
        json['forecast']['txt_forecast']['forecastday'][0]['fcttext'],
        json['forecast']['txt_forecast']['forecastday'][1]['title'],
        json['forecast']['txt_forecast']['forecastday'][1]['fcttext'],
        )
        
        return output
    def clearcache(self,irc,msg,args):
        self.pastweatherlookups = {}
        self.pastforecastlookups = {}
        irc.reply("Cleared Cache")
        
    weathercacheclear = wrap(clearcache)
    
    
    def weather(self,irc,msg,args,text):
        now = datetime.datetime.now(pytz.utc)
        if text in self.pastweatherlookups:
            l = self.pastweatherlookups[text]
            delta = now-l[0]
            if delta.seconds < CACHE_PERIOD:
                rep = "%s (cached)" % l[1]
                irc.reply(rep)
                return
            
        data,success = self.weather_lookup(text)
        if not success:
            irc.reply(data)
        else:
            reply = self.weather_formatting(data)
            self.pastweatherlookups[text] = [datetime.datetime.now(pytz.utc),reply]
            irc.reply(reply)
        
    weather = wrap(weather, ['text'])
    
    def forcecast(self,irc,msg,args,text):
        now = datetime.datetime.now(pytz.utc)
        #get the flippant text
        openstring = "%s/flippant/" % (os.getcwd())
        f_msgset_a = []
        for i in range(3):
            replies = open(openstring + str(i),"r").readlines()
            f_msgset_a.append(replies)
        #get the weather from cache
        
        if text in self.pastforecastlookups:
            l = self.pastforecastlookups[text]
            delta = now-l[0]
            if delta.seconds < CACHE_PERIOD:
                data = l[1]
                success = True
                setcache = False
            else:
                data,success = self.weather_lookup(text)
                setcache = True
        else:
            data,success = self.weather_lookup(text)
            setcache = True
            
        if not success:
            irc.reply(data)
            return
            
        # get locale
        #print data
        location = data['current_observation']['observation_location']['full']
        weather = data['current_observation']['weather']

        
        temp = data['current_observation']['temp_c']
        temp_str = data['current_observation']['temperature_string']
        #textualize temperature
        if temp > 50:
            f_temp = "LIKE THE FUCKING SUN"
            beratement = 0
        elif 40 <= temp <= 50:
            f_temp = "HOT"
            beratement = 1
        elif 30 <= temp < 40:
            f_temp = "warm"
            beratement = 2
        elif 20 <= temp < 30:
            f_temp = "splendid"
            beratement = 2 
        elif 10 <= temp < 20:
            f_temp = "cool"
            beratement = 1
        elif 0 <= temp < 10:
            f_temp = "cold"
            beratement = 0
        else:
            f_temp = "BALLS COLD"
            beratement = 0


        #textualize windspeed
        try:
            f_wd = data['current_observation']['wind_dir']
            ws = data['current_observation']['wind_mph0']
        except:
            f_wd = ''
            ws = 0
        if ws <= 2:
            f_ws = "pretty calm air"
        elif 2 < ws <= 10:
            f_ws = "a breeze"
        elif 10 < ws <= 30:
            f_ws = "a decent breeze"
        elif 30 < ws <= 40:
            f_ws = "a strong wind"
        elif 40 < ws <= 65:
            f_ws = "a gale"
        else:
            f_ws = "A FUCKING HURRICANE UP IN YOUR SHIT"
        
        #get dar flippant
        flippant = choice(f_msgset_a[beratement]).strip()
        try:
            flippant = flippant.split("~!~")[1] #tied into GQuote through simlinks
        except:
            flippant = flippant
        
            
        #combine our terms    
        if f_wd == 'Variable':
            final_output = 'In %s it\'s %s and %s {%s} with %s from fucking everywhere. %s' % (location,weather,f_temp,temp_str.replace(' ',''),f_ws,flippant)
        elif f_wd == '':
            final_output = 'In %s it\'s %s and %s {%s} with %s. %s' % (location,weather,f_temp,temp_str.replace(' ',''),f_ws,flippant)
        else:
            final_output = 'In %s it\'s %s and %s {%s} with %s from the %s. %s' % (location,weather,f_temp,temp_str.replace(' ',''),f_ws,f_wd,flippant)
            
        if setcache:
            self.pastforecastlookups[text] = [datetime.datetime.now(pytz.utc),data]
        else:
            final_output = final_output + " (cached)"
        #irc.reply(final_output)
        irc.sendMsg(ircmsgs.privmsg(msg.args[0],final_output))
    forecast=wrap(forcecast, ['text'])


Class = Weather2014


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
