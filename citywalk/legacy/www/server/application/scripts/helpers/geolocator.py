from geopy.geocoders import GoogleV3
import os


class Geolocator():

    def __init__(self):
        self.geolocator = GoogleV3(api_key=os.environ.get('GOOGLE_GEOCODING_API_KEY'))
        pass

    def get_lat_lng_from_address(self, province, city, address1, language):
        print('{}, {}, {}'.format(province, city, address1))
        location = self.geolocator.geocode(query='{}, {}, {}'.format(province, city, address1), language=language)
        return location.latitude, location.longitude

    def get_address_from_lat_lng(self, lat, lng, language):
        location = self.geolocator.reverse(query='{} {}'.format(str(lat), str(lng)), language=language)
        return location.raw
