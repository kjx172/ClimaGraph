import openmeteo_requests
from geopy.geocoders import Nominatim

import matplotlib.pyplot as plt

import requests_cache
import pandas as pd
from retry_requests import retry

#chatgpt inspo: fun facts?

#Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

url = "https://api.open-meteo.com/v1/forecast"
geolocator = Nominatim(user_agent='weather_data')

#holds number of cities user wants to compare
num_cities = int(input("Enter the number of cites you'd like to compare: "))
cities_list = []
city_count = 1

#--------------------------------------------------------------------------------------------#

while num_cities != 0:
    #gets longitude and latitude from user city input
    user_city = input(f"Enter the name of city #{city_count}: ")
    location = geolocator.geocode(user_city)
    city_lat = location.raw['lat']
    city_lon = location.raw['lon']

    #Desired weather variables and specifications in params
    params = {
        "latitude": city_lat,
        "longitude": city_lon,
        "daily": ["temperature_2m_max", "temperature_2m_min", "uv_index_max", "precipitation_sum", "wind_speed_10m_max"],
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "auto",
        "start_date": "2024-06-07",
        "end_date": "2024-06-24"
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process daily data. The order of variables needs to be the same as requested.
    daily = responses[0].Daily()

    # Extract data for each variable and convert to Numpy arrays
    daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()
    daily_uv_index_max = daily.Variables(2).ValuesAsNumpy()
    daily_precipitation_sum = daily.Variables(3).ValuesAsNumpy()
    daily_wind_speed_10m_max = daily.Variables(4).ValuesAsNumpy()

    #create a daily_data dictionary and add the extracted data to dictionary
    daily_data = {"date": pd.date_range(
        start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
        end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = daily.Interval()),
        inclusive = "left"
    )}
    daily_data["temperature_2m_max"] = daily_temperature_2m_max
    daily_data["temperature_2m_min"] = daily_temperature_2m_min
    daily_data["uv_index_max"] = daily_uv_index_max
    daily_data["precipitation_sum"] = daily_precipitation_sum
    daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max

    daily_dataframe = pd.DataFrame(data = daily_data)
    cities_list.append(daily_dataframe)
    num_cities -= 1
    city_count += 1

#change to output to text file
for city in cities_list:
    print(city)

#-------------------------------------------------------------------------------------------------------------------#

'''
# Line Plot for temperatures
plt.figure(figsize=(12, 6))
plt.plot(daily_data1['date'], daily_data1['temperature_2m_max'], label='Max Temperature C1')
plt.plot(daily_data2['date'], daily_data2['temperature_2m_max'], label='Max Temperature C2')
plt.xlabel('Date')
plt.ylabel('Temperature (F)')
plt.title('Daily Max Temperatures for C1 vs C2')
plt.legend()
plt.savefig('temperature_plot.png')
print("File has been saved")
'''