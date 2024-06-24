import openmeteo_requests
from geopy.geocoders import Nominatim

import matplotlib.pyplot as plt

import requests_cache
import pandas as pd
from retry_requests import retry

def WriteToFile(cities_dict):
    f = open("database_file.txt", "w")
    for key, value in cities_dict.items():
        f.write(key + '\n' + str(value) + '\n')
    f.close()


#Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

url = "https://api.open-meteo.com/v1/archive"
geolocator = Nominatim(user_agent='weather_data')

user_start = input("Enter a start date (format: yyyy-mm-dd): ")
user_end = input("Enter an end date (format: yyyy-mm-dd): ")

#holds number of cities user wants to compare
num_cities = int(input("Enter the number of cites you'd like to compare: "))
cities_dict = {}
city_count = 1

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
        "start_date": user_start,
        "end_date": user_end
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
    cities_dict[location.raw['display_name'] + "(User entered: " + user_city + ")"] = daily_dataframe
    num_cities -= 1
    city_count += 1

#change to output to text file
WriteToFile(cities_dict)

#outputing the list of variables
dataframe_list = list(cities_dict.values())
temp_col = dataframe_list[0]
for i, variable in enumerate(temp_col):
    print(f"{i + 1}. {variable}")

selected_index = int(input("Enter which variable index you would like to compare for the selected cities: "))

#finding the vairable name for the given index
target_var = ""
for j,variable in enumerate(temp_col):
    if j == selected_index - 1:
        target_var = variable
        break


#generates graph for variable
plt.figure(figsize=(12, 6))
for city, dataframe in cities_dict.items():
    plt.plot(dataframe['date'], dataframe[target_var], label=target_var + " " + city)
plt.xlabel('Date')
plt.ylabel(target_var)
plt.title(target_var + " over time")
plt.legend()
plt.savefig(target_var + '_plot.png')
print("File has been saved")
