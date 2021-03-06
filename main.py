#!/usr/bin/env python
#
#Precipa is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#Precipa is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with Precipa.  If not, see <http://www.gnu.org/licenses/>

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
import urllib2, urllib
import xml.dom.minidom
import os
import random
import re

class Precipa(webapp.RequestHandler):
	flickr_api_key = "7c04ca9148bb66f16350a3243fcaf77d"
	flickr_api_secret = "b8e62385362ea137"
	
	def get(self):
		city_list = self.get_city_list(self.request.get("location", default_value = "Santiago, Chile"));
		if(city_list):
			for city in city_list:
				if(city["weather"]):
					city_photos = self.get_photos(city)
					if(city_photos):
						random.seed();
						pick_photo = random.randint(0, len(city_photos))
						photo_url = city_photos[pick_photo][0]
						flickr_url = city_photos[pick_photo][1]
						template_values = {
							'temperature': city["weather"]["temperature"],
							'city': city["name"] + ", " + city["country"],
							'photo': photo_url,
							'link': flickr_url,
							'condition': city["weather"]["condition"]
						}
						path = os.path.join(os.path.dirname(__file__), 'main.html')
						self.response.out.write(template.render(path, template_values))
						break;
		else:
			self.response.out.write("City not found...")
	
	def get_city_list(self, cityname):
		name = cityname.replace(" ", "%20");
		data = urllib2.urlopen("http://where.yahooapis.com/geocode?q=" + name).read()
		parsed_data = xml.dom.minidom.parseString(data)
		found = parsed_data.getElementsByTagName('Found')[0].firstChild.nodeValue
		if(found > 0):
			w_list = []
			woeid = parsed_data.getElementsByTagName('Result')
			for w in woeid:
				w_dict = {}
				w_dict["name"] =  w.getElementsByTagName("city")[0].firstChild.nodeValue
				#w_dict["state"] = w.getElementsByTagName("state")[0].firstChild.nodeValue
				w_dict["country"] = w.getElementsByTagName("country")[0].firstChild.nodeValue
				woeid = w.getElementsByTagName("woeid")[0].firstChild.nodeValue
				w_dict["weather"] = self.get_city_weather(woeid);
				w_list.append(w_dict);
			return w_list
		return False
	
	def get_city_weather(self, woeid):
		data = urllib2.urlopen("http://weather.yahooapis.com/forecastrss?u=c&w="+str(woeid)).read()
		parsed_data = xml.dom.minidom.parseString(data)
		found = (parsed_data.getElementsByTagName("title")[0].firstChild.nodeValue != "Yahoo! Weather - Error")
		if(found):
			w_list = {}
			condition = parsed_data.getElementsByTagName("yweather:condition")[0]
			w_list["temperature"] = condition.getAttribute("temp")
			w_list["condition"] = condition.getAttribute("text")
			if(w_list["condition"] == "Fair"):
				w_list["condition"] = "Nice Day"
			elif(w_list["condition"] == "Smoke"):
				w_list["condition"] = "Smog"
			w_list["unit"] = parsed_data.getElementsByTagName("yweather:units")[0].getAttribute("temperature")
			return w_list
		return False
		
	
	def get_photos(self, city_info):
	
		params = {
			"method":"flickr.photos.search",
			"api_key":self.flickr_api_key,
			"text": city_info["country"] + " " + city_info["name"] + " " + city_info["weather"]["condition"],
			"tags": city_info["country"] + ", " + city_info["name"] + city_info["weather"]["condition"] + ", outdoors, landscape, weather",
			"media": "photos",
			"content_type": "1",
		}
		
		uri	= "http://api.flickr.com/services/rest/?" + urllib.urlencode(params)
		data = urllib2.urlopen(uri).read()
		parsed_data = xml.dom.minidom.parseString(data.decode("ascii", "ignore"))
		
		photo_list = parsed_data.getElementsByTagName("photo")
		urls_list = []
		if(len(photo_list) > 0):
			for p in photo_list:
				photo_id = p.getAttribute("id")
				photo_server = p.getAttribute("server")
				photo_secret = p.getAttribute("secret")
				photo_owner = p.getAttribute("owner");
				photo_farm = p.getAttribute("farm")
				photo_urls = "http://farm" + photo_farm + ".staticflickr.com/" + photo_server + "/" + photo_id + "_" + photo_secret + "_b.jpg", "http://www.flickr.com/photos/" + photo_owner + "/" + photo_id
				urls_list.append(photo_urls)
			return urls_list
		return False

class GetOSecret(webapp.RequestHandler):
	def get(self):
		photo_id = self.request.get("id")
		ose = self.get_osecret(photo_id)
		if(ose):
			self.response.out.write(ose)
		else:
			self.response.out.write("No existe original")
			
	def get_osecret(self, id):
		uri = "http://flickr.com/photo.gne?id="+str(id)
		data = urllib2.urlopen(uri).read()
		m = re.search('"_[0-9a-f]*_o.jpg"', data)
		if(m==None):
			return False
		else:
			return m.group(0).split("_")[1]

def main():
	application = webapp.WSGIApplication([('/', Precipa), ('/secret', GetOSecret),], debug=True)
	util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
