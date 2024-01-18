import requests


def loc_request(IP):
    with open('API_KEY_GEO.txt') as f:
        key = f.readline()

    url = 'http://api.ipstack.com/' + IP
    getparams = {
        'access_key': key
    }
    response = requests.get(url=url, params=getparams)
    data = response.json()
    lat = data['latitude']
    lon = data['longitude']
    return lat, lon


def weather_request(update_geo, IP):
    with open('API_KEY_WEATHER.txt') as f:
        key = f.readline()

    url = 'https://api.openweathermap.org/data/2.5/weather'
    if update_geo:
        lat, lon = loc_request(IP)
        with open('Saved_coords.txt', 'w') as f:
            f.write(str(lat) + ' ' + str(lon))
    else:
        with open('Saved_coords.txt') as f:
            lat, lon = list(map(float, f.read().split()))
    getparams = {
        'lat': lat,
        'lon': lon,
        'appid': key,
        'units': 'metric'
    }
    response = requests.get(url=url, params=getparams)
    data = response.json()
    print(data)
    return data