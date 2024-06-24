import openmeteo_requests
from geopy.geocoders import Nominatim

import matplotlib.pyplot as plt

import requests_cache
import pandas as pd
from retry_requests import retry

#Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

#--------------------------------------------------------------------------------------------#

#gets longitude and latitude from user city input
user_city1 = input("Enter the name of the first city: ")
geolocator1 = Nominatim(user_agent='weather_data')
location1 = geolocator1.geocode(user_city1)
city_lat1 = location1.raw['lat']
city_lon1 = location1.raw['lon']

#Desired weather variables and specifications in params
url = "https://api.open-meteo.com/v1/forecast"
params1 = {
	"latitude": city_lat1,
	"longitude": city_lon1,
	"daily": ["temperature_2m_max", "temperature_2m_min", "uv_index_max", "precipitation_sum", "wind_speed_10m_max"],
	"temperature_unit": "fahrenheit",
	"wind_speed_unit": "mph",
	"precipitation_unit": "inch",
    "timezone": "auto",
	"start_date": "2024-06-07",
	"end_date": "2024-06-24"
}
responses1 = openmeteo.weather_api(url, params=params1)

# Process daily data. The order of variables needs to be the same as requested.
daily1 = responses1[0].Daily()

# Extract data for each variable and convert to Numpy arrays
daily_temperature_2m_max1 = daily1.Variables(0).ValuesAsNumpy()
daily_temperature_2m_min1 = daily1.Variables(1).ValuesAsNumpy()
daily_uv_index_max1 = daily1.Variables(2).ValuesAsNumpy()
daily_precipitation_sum1 = daily1.Variables(3).ValuesAsNumpy()
daily_wind_speed_10m_max1 = daily1.Variables(4).ValuesAsNumpy()

#create a daily_data dictionary and add the extracted data to dictionary
daily_data1 = {"date": pd.date_range(
	start = pd.to_datetime(daily1.Time(), unit = "s", utc = True),
	end = pd.to_datetime(daily1.TimeEnd(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = daily1.Interval()),
	inclusive = "left"
)}
daily_data1["temperature_2m_max"] = daily_temperature_2m_max1
daily_data1["temperature_2m_min"] = daily_temperature_2m_min1
daily_data1["uv_index_max"] = daily_uv_index_max1
daily_data1["precipitation_sum"] = daily_precipitation_sum1
daily_data1["wind_speed_10m_max"] = daily_wind_speed_10m_max1

daily_dataframe1 = pd.DataFrame(data = daily_data1)
print(daily_dataframe1)

#-------------------------------------------------------------------------------------------------------------------#

#gets longitude and latitude from user city input
user_city2 = input("Enter the name of the second city: ")
geolocator2 = Nominatim(user_agent='weather_data')
location2 = geolocator2.geocode(user_city2)
city_lat2 = location2.raw['lat']
city_lon2 = location2.raw['lon']

#Desired weather variables and specifications in params
params2 = {
	"latitude": city_lat2,
	"longitude": city_lon2,
	"daily": ["temperature_2m_max", "temperature_2m_min", "uv_index_max", "precipitation_sum", "wind_speed_10m_max"],
	"temperature_unit": "fahrenheit",
	"wind_speed_unit": "mph",
	"precipitation_unit": "inch",
    "timezone": "auto",
	"start_date": "2024-06-07",
	"end_date": "2024-06-24"
}
responses2 = openmeteo.weather_api(url, params=params2)

# Process daily data. The order of variables needs to be the same as requested.
daily2 = responses2[0].Daily()

# Extract data for each variable and convert to Numpy arrays
daily_temperature_2m_max2 = daily2.Variables(0).ValuesAsNumpy()
daily_temperature_2m_min2 = daily2.Variables(1).ValuesAsNumpy()
daily_uv_index_max2 = daily2.Variables(2).ValuesAsNumpy()
daily_precipitation_sum2 = daily2.Variables(3).ValuesAsNumpy()
daily_wind_speed_10m_max2 = daily2.Variables(4).ValuesAsNumpy()

#create a daily_data dictionary and add the extracted data to dictionary
daily_data2 = {"date": pd.date_range(
	start = pd.to_datetime(daily2.Time(), unit = "s", utc = True),
	end = pd.to_datetime(daily2.TimeEnd(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = daily2.Interval()),
	inclusive = "left"
)}
daily_data2["temperature_2m_max"] = daily_temperature_2m_max2
daily_data2["temperature_2m_min"] = daily_temperature_2m_min2
daily_data2["uv_index_max"] = daily_uv_index_max2
daily_data2["precipitation_sum"] = daily_precipitation_sum2
daily_data2["wind_speed_10m_max"] = daily_wind_speed_10m_max2

daily_dataframe2 = pd.DataFrame(data = daily_data2)
print(daily_dataframe2)

#-----------------------------------------------------------------------------------#

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