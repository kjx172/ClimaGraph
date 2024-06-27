# Imports
from geopy.geocoders import Nominatim
import matplotlib.pyplot as plt
import requests_cache
import requests
import pandas as pd
from retry_requests import retry
from datetime import datetime
import warnings
from matplotlib.font_manager import FontProperties
import sqlite3
import csv
import time  # Added for time.sleep() usage

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


# Needed to find lat & long given city name
geolocator = Nominatim(user_agent='weather_data')


# Store data in a database file
def write_to_file(cities_dict):
    # Create or connect to the database
    conn = sqlite3.connect('weather_data.db')
    c = conn.cursor()

    # Create a new table for each city
    for city, dataframe in cities_dict.items():
        city_table = (
            city.replace(" ", "_")
                .replace(",", "")
                .replace("(", "")
                .replace(")", "")
                .replace("User_entered:", "")
                .replace("-", "_")
                .replace("__", "_")
                .replace("'", "")
        )

        c.execute(f'''CREATE TABLE IF NOT EXISTS {city_table} (
                        date TEXT,
                        temperature_2m_max REAL,
                        temperature_2m_min REAL,
                        uv_index_max REAL,
                        precipitation_sum REAL,
                        wind_speed_10m_max REAL)''')

        # Write the dataframe to the table
        dataframe.to_sql(city_table, conn, if_exists='replace', index=False)

    conn.commit()
    conn.close()


def query_database():
    # Connect to the SQLite database
    conn = sqlite3.connect('weather_data.db')
    c = conn.cursor()

    # Getting city name
    while True:
        user_input_city = input(
            "Enter the name of the city you want to query: "
        )

        # Attempt to find a city in the database that matches
        # Or partially matches the user input
        c.execute(
            f"SELECT name FROM sqlite_master WHERE type='table';"
            )
        tables = c.fetchall()
        city_table = None
        for table in tables:
            if user_input_city in table[0]:
                city_table = table[0]
                break

        if not city_table:
            print(
                "Error: City not found in database. "
                "Please enter a valid city name."
                )
            continue

        try:
            break
        except ValueError:
            print(
                "Error: City not found in database."
                "Please enter a valid city name."
                )

    # Get the date range the user wants
    while True:
        start_date = input(
            "Enter the start date (format: yyyy-mm-dd): "
            )
        end_date = input(
            "Enter the end date (format: yyyy-mm-dd): "
            )

        try:
            # Validate the date format
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
            break
        except ValueError:
            print(
                "Error: Invalid date format."
                "Please enter the date in yyyy-mm-dd format."
            )

    # SQL query to select data within the specified date range
    query = f'''SELECT * FROM {city_table}
                WHERE date BETWEEN '{start_date}' AND '{end_date}' '''
    c.execute(query)
    results = c.fetchall()

    # Close the database connection
    conn.close()

    # Save results to CSV file
    if results:
        # Get column names from cursor description
        col_names = [desc[0] for desc in c.description]

        # Write results to CSV file
        filename = (
            f"{user_input_city}_weather_data_{start_date}_to_{end_date}.csv"
        )

        with open(filename, 'w', newline='') as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(col_names)  # Write column headers
            csv_writer.writerows(results)   # Write data rows

        print(f"Results saved to {filename}")
        return
    else:
        print("No results found for the specified criteria.")


# Checks if date is before 2016 (Archive API vs Forecast API)
def check_date(date_str):
    str_list = date_str.split("-")
    year = int(str_list[0])

    if year < 2016:
        return True
    else:
        return False
    str_list = date_str.split("-")
    year = int(str_list[0])

    if year < 2016:
        return True
    else:
        return False


# Ensures the date is in the correct format
# Return the str as it's needed later
def ensure_valid_date(prompt):
    while True:
        user_input = input(prompt)
        try:
            valid_date = datetime.strptime(user_input, "%Y-%m-%d")
            return user_input
        except ValueError:
            print(
                "Invalid date format."
                "Please enter the date in yyyy-mm-dd format."
            )
    while True:
        user_input = input(prompt)
        try:
            valid_date = datetime.strptime(user_input, "%Y-%m-%d")
            return user_input
        except ValueError:
            print(
                "Invalid date format."
                "Please enter the date in yyyy-mm-dd format."
            )


# Checks if the date range is valid
def check_range(user_start, user_end):
    error_code = 0
    user_start_datetime = datetime.strptime(user_start, "%Y-%m-%d")
    user_end_datetime = datetime.strptime(user_end, "%Y-%m-%d")

    # Check if start date is after end date
    if user_end_datetime < user_start_datetime:
        error_code = -1

    # Check if start date is before 1940
    minimum_start = datetime.strptime("1940-01-01", "%Y-%m-%d")
    if user_start_datetime < minimum_start:
        error_code = -2

    # Check if end date is after the current date
    if user_end_datetime > datetime.now():
        error_code = -3

    return error_code


# Creates a graph based on the cities and variable given
def create_graph(cities_dict, target_var):
    # Warning filter for city names with unrecognized characters
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        plt.figure(figsize=(12, 6))
        for city, dataframe in cities_dict.items():
            plt.plot(
                dataframe['date'], dataframe[target_var],
                label=target_var + " " + city
            )

        plt.xlabel('Date')
        plt.ylabel(target_var)
        plt.title(target_var + " over time")
        plt.legend()
        plt.savefig(target_var + '_plot.png')

        # Check if any UserWarning was
        # issued and replace it with a custom message
        for warning in w:
            if issubclass(warning.category, UserWarning):
                if "Glyph" in str(warning.message):
                    print(
                        "Warning: cannot properly display "
                        "one or more characters in the city name"
                        )
                break

    print("Graph has been saved")


# Uses the weather forecast API for start dates after 2016-01-01
def weather_forecast(user_start, user_end):
    url = "https://api.open-meteo.com/v1/forecast"

    # Input validation for the number of cities to graph
    while True:
        try:
            num_cities = int(input(
                "Enter the number of cities you'd like to graph "
                "(warning: more than 5 cities might "
                "hit the minute rate limit): "
            ))
            break
        except ValueError:
            print("Error: Please enter an integer")

    cities_dict = {}
    city_count = 1

    while num_cities != 0:
        # Gets longitude and latitude from user city input
        # Input validation for city name
        while True:
            user_city = input(f"Enter the name of city #{city_count}: ")
            try:
                location = geolocator.geocode(user_city)
                city_lat = location.raw['lat']
                city_lon = location.raw['lon']
                break
            except AttributeError:
                print(
                    "Error: City name not recognized. "
                    "Please enter a valid city name."
                )

        # Desired weather variables and specifications in params
        params = {
            "latitude": city_lat,
            "longitude": city_lon,
            "daily": [
                "temperature_2m_max", "temperature_2m_min", "uv_index_max",
                "precipitation_sum", "wind_speed_10m_max"],
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "auto",
            "start_date": user_start,
            "end_date": user_end
        }
        try:
            response = openmeteo.weather_api(url, params=params)
        except Exception as e:  # Catching all exceptions
            sample_error = (
                'Minutely API request limit exceeded. '
                'Please try again in one minute.'
            )
            # Handle any exception here
            if hasattr(e, 'error_data'):
                if getattr(e, 'error_data', {}).get('reason') == sample_error:
                    print(
                        "API limit exceeded for this minute. "
                        "Please try again in one minute."
                    )
                    time.sleep(60)  # Wait for one minute before retrying
            else:
                raise  # Re-raise the exception if not related to API limit

        if not response:
            print(
                "No response from server. "
                "Please enter valid city name."
            )
            continue

        # Process daily data
        # The order of variables needs to be the same as requested.
        daily = response[0].Daily()

        # Extract data for each variable and convert to Numpy arrays
        daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
        daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()
        daily_uv_index_max = daily.Variables(2).ValuesAsNumpy()
        daily_precipitation_sum = daily.Variables(3).ValuesAsNumpy()
        daily_wind_speed_10m_max = daily.Variables(4).ValuesAsNumpy()

        # Create a daily_data dictionary
        # Add the extracted data to dictionary
        daily_data = {"date": pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left"
        )}
        daily_data["temperature_2m_max"] = daily_temperature_2m_max
        daily_data["temperature_2m_min"] = daily_temperature_2m_min
        daily_data["uv_index_max"] = daily_uv_index_max
        daily_data["precipitation_sum"] = daily_precipitation_sum
        daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max

        # Place the city name and the dataframe into a dictionary
        daily_dataframe = pd.DataFrame(data=daily_data)
        cities_dict[
            f"{location.raw['display_name']} (User entered: {user_city})"
        ] = daily_dataframe

        num_cities -= 1
        city_count += 1

    # Output to db file
    write_to_file(cities_dict)

    return cities_dict


# Uses the weather archive API for start dates before 2016-01-01
def weather_archive(user_start, user_end):
    url = "https://archive-api.open-meteo.com/v1/archive"

    # Input validation for number of cities to graph
    while True:
        try:
            num_cities = int(input(
                "Enter the number of cities you'd like to graph "
                "(warning: more than 5 cities might "
                "hit the minute rate limit): "
            ))
            break
        except ValueError:
            print("Error: Please enter an integer")

    cities_dict = {}
    city_count = 1

    while num_cities != 0:
        # Gets longitude and latitude from user city input
        # Input validation for city name
        while True:
            user_city = input(f"Enter the name of city #{city_count}: ")
            try:
                location = geolocator.geocode(user_city)
                city_lat = location.raw['lat']
                city_lon = location.raw['lon']
                break
            except AttributeError:
                print(
                    "Error: City name not recognized. "
                    "Please enter a valid city name."
                    )

        # Desired weather variables and specifications in params
        params = {
            "latitude": city_lat,
            "longitude": city_lon,
            "daily": [
                "temperature_2m_max", "temperature_2m_min",
                "temperature_2m_mean", "precipitation_sum",
                "wind_speed_10m_max", "shortwave_radiation_sum"],
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "auto",
            "start_date": user_start,
            "end_date": user_end
        }
        try:
            response = openmeteo.weather_api(url, params=params)
        except Exception as e:  # Catching all exceptions
            sample_error = (
                'Minutely API request limit exceeded. '
                'Please try again in one minute.'
            )
            # Handle any exception here
            if hasattr(e, 'error_data'):
                if getattr(e, 'error_data', {}).get('reason') == sample_error:
                    print(
                        "API limit exceeded for this minute. "
                        "Please try again in one minute."
                    )
                    time.sleep(60)  # Wait for one minute before retrying
            else:
                raise  # Re-raise the exception if not related to API limit

        if not response:
            print(
                "No response from server. "
                "Please enter valid city name."
                )
            continue

        # Process daily data.
        # The order of variables needs to be the same as requested.
        daily = response[0].Daily()

        daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
        daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()
        daily_temperature_2m_mean = daily.Variables(2).ValuesAsNumpy()
        daily_precipitation_sum = daily.Variables(3).ValuesAsNumpy()
        daily_wind_speed_10m_max = daily.Variables(4).ValuesAsNumpy()
        daily_shortwave_radiation_sum = daily.Variables(5).ValuesAsNumpy()

        # Create a daily_data dictionary
        # add the extracted data to dictionary
        daily_data = {"date": pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left"
        )}
        daily_data["temperature_2m_max"] = daily_temperature_2m_max
        daily_data["temperature_2m_min"] = daily_temperature_2m_min
        daily_data["temperature_2m_mean"] = daily_temperature_2m_mean
        daily_data["precipitation_sum"] = daily_precipitation_sum
        daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max
        daily_data["shortwave_radiation_sum"] = daily_shortwave_radiation_sum

        # Place the city name and the dataframe into a dictionary
        daily_dataframe = pd.DataFrame(data=daily_data)
        cities_dict[
            f"{location.raw['display_name']} (User entered: {user_city})"
        ] = daily_dataframe

        num_cities -= 1
        city_count += 1

    # Output to db file
    write_to_file(cities_dict)

    return cities_dict


def main():
    database_empty = True
    while True:
        # Prompt user to either add new data or query the database, or exit
        choice = input(
            "Enter '1' to add new data,"
            " '2' to query the database,"
            " or '3' to exit: "
        )
        if choice == '1':
            while True:
                user_start = ensure_valid_date(
                    "Enter a start date (format: yyyy-mm-dd): "
                )
                user_end = ensure_valid_date(
                    "Enter an end date (format: yyyy-mm-dd): "
                )
                error_code = check_range(user_start, user_end)

                if error_code == 0:
                    break
                elif error_code == -1:
                    print(
                        "Error: "
                        "Ensure that the start date is before the end date."
                    )
                elif error_code == -2:
                    print("Error: Start date cannot be before 1940-01-01.")
                elif error_code == -3:
                    print(
                        f"Error: End date cannot be after the current date "
                        f"({datetime.now().date()})."
                        )

            # If the start date is before 2016, use the archive API
            pre_2016 = check_date(user_start)
            if pre_2016:
                cities_dict = weather_archive(user_start, user_end)
            else:
                cities_dict = weather_forecast(user_start, user_end)

            # Output the list of variables
            dataframe_list = list(cities_dict.values())
            temp_col = dataframe_list[0]
            for i, variable in enumerate(temp_col):
                print(f"{i + 1}. {variable}")

            # Input validation for variable index
            while True:
                try:
                    selected_index = int(input(
                        "Enter which variable index you would "
                        "like to graph for the selected cities: "
                    ))
                except ValueError:
                    print("Error: Please enter an integer index.")
                    continue

                if selected_index in range(1, i + 1):
                    break
                else:
                    print("Error: Please enter an index in range.")

            # Find the variable name for the given index
            target_var = ""
            for j, variable in enumerate(temp_col):
                if j == selected_index - 1:
                    target_var = variable
                    break
            create_graph(cities_dict, target_var)

            database_empty = False

        elif choice == '2':
            if database_empty:
                print(
                    "Database empty, please add data before "
                    "attempting to query the database"
                )
            else:
                query_database()
        elif choice == '3':
            exit()
        else:
            print("Invalid choice. Please enter '1', '2', or '3'.")


if __name__ == "__main__":
    # Globally suppress the specific UserWarning
    warnings.filterwarnings(
        "ignore", category=UserWarning,
        message=r"Glyph .* missing from font\(s\) DejaVu Sans"
    )
    main()
