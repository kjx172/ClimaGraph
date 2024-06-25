import openmeteo_requests
from geopy.geocoders import Nominatim

import matplotlib.pyplot as plt

import requests_cache
import pandas as pd
from retry_requests import retry
from datetime import datetime

#----------------------------------------------------#

#Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

#needed to find lat & long given city name
geolocator = Nominatim(user_agent='weather_data')

#---------------------helper functions-----------------------------#
def EnsureValidDate(prompt):

    #Input validation for date entry
    while True:
        user_input = input(prompt)
        try:
            # Try to parse the input into a datetime object
            valid_date = datetime.strptime(user_input, "%Y-%m-%d")
            return user_input
        except ValueError:
            print("Invalid date format. Please enter the date in yyyy-mm-dd format.")

def WriteToFile(cities_dict):
    f = open("database_file.txt", "w")
    for key, value in cities_dict.items():
        f.write(key + '\n' + str(value) + '\n')
    f.close()

#checks if date is before 2016
def CheckDate(date_str):
    str_list = date_str.split("-")
    year = int(str_list[0])
    
    if year < 2016:
        return True
    else:
        return False

#checks if end date is after the start range 
def CheckRange(user_start, user_end):
    error_code = 0

    #Checks if start date is before end date
    try:
        start_date = datetime.strptime(user_start, "%Y-%m-%d")
        end_date = datetime.strptime(user_end, "%Y-%m-%d")
        if end_date >= start_date:
                error_code = -1
    except ValueError:
        error_code = -1

    #Checks if end date is before start date
    if end_date < start_date:
        error_code = -1

    #Check if start date is before 1940
    minimum_start = datetime.strptime("1940-01-01", "%Y-%m-%d")
    if start_date < minimum_start:
        error_code = -2

    #Check if end date is before current date
    if end_date < datetime.now():
        error_code = -3

    return 0

def CreateGraph(cities_dict, target_var):
    plt.figure(figsize=(12, 6))
    for city, dataframe in cities_dict.items():
        plt.plot(dataframe['date'], dataframe[target_var], label=target_var + " " + city)
    plt.xlabel('Date')
    plt.ylabel(target_var)
    plt.title(target_var + " over time")
    plt.legend()
    plt.savefig(target_var + '_plot.png')
    print("File has been saved")

#--------------------------------------------------#

#uses the weather forcast API for start dates after 2016-01-01
def WeatherForcast(user_start, user_end):
    url = "https://api.open-meteo.com/v1/forecast"

    #Input validation for the number of cities to graph
    while True:
        try:
            num_cities = int(input("Enter the number of cites you'd like to graph: "))
            break
        except ValueError:
            print("Error: Please enter a integer")
       
    cities_dict = {}
    city_count = 1

    while num_cities != 0:
        #gets longitude and latitude from user city input

        #Input validation for city name
        while True:
            user_city = input(f"Enter the name of city #{city_count}: ")
            try:
                location = geolocator.geocode(user_city)
                city_lat = location.raw['lat']
                city_lon = location.raw['lon']
                break
            except AttributeError:
                print("Error: City name not recognized. Please enter a valid city name.")

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
        response = openmeteo.weather_api(url, params=params)

        if not response:
            print("No response from server. Please enter valid city name.")
            continue

        # Process daily data. The order of variables needs to be the same as requested.
        daily = response[0].Daily()

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

        #place the city name and the dataframe into a dictionary
        daily_dataframe = pd.DataFrame(data = daily_data)
        cities_dict[location.raw['display_name'] + "(User entered: " + user_city + ")"] = daily_dataframe
        num_cities -= 1
        city_count += 1

    #change to output to text file
    WriteToFile(cities_dict)
    return cities_dict

#uses the weather archive API for start dates before 2016-01-01
def WeatherArchive(user_start, user_end):
    url = "https://archive-api.open-meteo.com/v1/archive"

    #Input validation for number of cities to graph
    while True:
        try:
            num_cities = int(input("Enter the number of cites you'd like to graph: "))
            break
        except ValueError:
            print("Error: Please enter a integer")

    cities_dict = {}
    city_count = 1

    while num_cities != 0:
        #gets longitude and latitude from user city input

        #Input validation for city name
        while True:
            user_city = input(f"Enter the name of city #{city_count}: ")
            try:
                location = geolocator.geocode(user_city)
                city_lat = location.raw['lat']
                city_lon = location.raw['lon']
                break
            except AttributeError:
                print("Error: City name not recognized. Please enter a valid city name.")

        #Desired weather variables and specifications in params
        params = {
            "latitude": city_lat,
            "longitude": city_lon,
            "daily": ["temperature_2m_max", "temperature_2m_min", "temperature_2m_mean", "precipitation_sum", "wind_speed_10m_max", "shortwave_radiation_sum"],
	        "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "auto",
            "start_date": user_start,
            "end_date": user_end
        }
        response = openmeteo.weather_api(url, params=params)

        if not response:
            print("No response from server. Please enter valid city name.")
            continue

        # Process daily data. The order of variables needs to be the same as requested.
        daily = response[0].Daily()

        daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
        daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()
        daily_temperature_2m_mean = daily.Variables(2).ValuesAsNumpy()
        daily_precipitation_sum = daily.Variables(3).ValuesAsNumpy()
        daily_wind_speed_10m_max = daily.Variables(4).ValuesAsNumpy()
        daily_shortwave_radiation_sum = daily.Variables(5).ValuesAsNumpy()

        #create a daily_data dictionary and add the extracted data to dictionary
        daily_data = {"date": pd.date_range(
            start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
            end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
            freq = pd.Timedelta(seconds = daily.Interval()),
            inclusive = "left"
        )}
        daily_data["temperature_2m_max"] = daily_temperature_2m_max
        daily_data["temperature_2m_min"] = daily_temperature_2m_min
        daily_data["temperature_2m_mean"] = daily_temperature_2m_mean
        daily_data["precipitation_sum"] = daily_precipitation_sum
        daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max
        daily_data["shortwave_radiation_sum"] = daily_shortwave_radiation_sum

        #place the city name and the dataframe into a dictionary
        daily_dataframe = pd.DataFrame(data = daily_data)
        cities_dict[location.raw['display_name'] + "(User entered: " + user_city + ")"] = daily_dataframe
        num_cities -= 1
        city_count += 1

    #change to output to text file
    WriteToFile(cities_dict)

    return cities_dict

#-------------------------------------------------------------------------------------------#

def main():
    while True:
        user_start = EnsureValidDate("Enter a start date (format: yyyy-mm-dd): ")
        user_end = EnsureValidDate("Enter an end date (format: yyyy-mm-dd): ")
        error_code = CheckRange(user_start, user_end)
        if error_code == 0:
            break
        elif error_code == -1:
            print("Error: Ensure that start date is before end date and that both dates follow the format.")
        elif error_code == -2:
            print("Error: Start date cannot precede 1940-01-01.")
        elif error_code == -3:
            print("Error: End date cannot surpass the current date.")
        else:
            print("Error: Ensure that end date is greater than or equal to start date.")

    #if date is before 2016, use the archive api
    pre_2016 = CheckDate(user_start)
    if pre_2016:
        cities_dict = WeatherArchive(user_start, user_end)
    else:
        cities_dict = WeatherForcast(user_start, user_end)

    #outputing the list of variables
    dataframe_list = list(cities_dict.values())
    temp_col = dataframe_list[0]
    for i, variable in enumerate(temp_col):
        print(f"{i + 1}. {variable}")

    #Input validation for variable index
    while True:
        try:
           selected_index = int(input("Enter which variable index you would like to graph for the selected cities: "))
        except ValueError: 
            print("Error: Please enter an integer index.")
            continue

        if selected_index in range(1, i + 1):
            break
        else:
            print("Error: Please enter an index in range.")

    #finding the variable name for the given index
    target_var = ""
    for j,variable in enumerate(temp_col):
        if j == selected_index - 1:
            target_var = variable
            break

    CreateGraph(cities_dict, target_var)

if __name__ == "__main__":
    main()