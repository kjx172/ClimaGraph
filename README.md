# Climagraph

Climagraph is a Python-based application designed to visualize weather data over time for various cities. It allows users to query weather data from both forecast and historical data sources, store the data in a local SQLite database, and generate graphical representations of selected weather variables.

## Features

- Retrieve weather data for multiple cities using the Open-Meteo API.
- Store weather data in a local SQLite database.
- Query the database for specific cities and date ranges.
- Generate graphs of weather variables over time.
- Handle API rate limits and retry requests automatically.
- Validate user input for city names and dates.

## Installation

To get started with Climagraph, follow these steps:

1. **Clone the repository:**

    ```bash
    git clone https://github.com/kjx172/ClimaGraph.git
    cd ClimaGraph
    ```

2. **Install the required dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. **Run the application:**

    ```bash
    python3 ClimaGraph.py
    ```

2. **Follow the on-screen prompts to either add new data or query the database:**

    - **Add new data:** 
        - Enter a start date and an end date.
        - Specify the number of cities you want to add.
        - Enter the names of the cities.
        - Select the weather variable you want to graph.
        
    - **Query the database:** 
        - Enter the name of the city.
        - Enter the start date and end date for the query.
        - The results will be saved to a CSV file.

## Example

To add weather data for two cities from 1940-01-01 to 2024-01-01:

```plaintext
Enter '1' to add new data, '2' to query the database, or '3' to exit: 1
Enter a start date (format: yyyy-mm-dd): 1940-01-01
Enter an end date (format: yyyy-mm-dd): 2020-01-01
Enter the number of cities you'd like to graph: 2
Enter the name of city #1: New York
Enter the name of city #2: Los Angeles
1. temperature_2m_max
2. temperature_2m_min
3. uv_index_max
4. precipitation_sum
5. wind_speed_10m_max
Enter which variable index you would like to graph for the selected cities: 1
Graph has been saved
```

To query the database for weather data in New York from 2000-01-01 to 2010-01-01:

```plaintext
Enter '1' to add new data, '2' to query the database, or '3' to exit: 2
Enter the name of the city you want to query: New York
Enter the start date (format: yyyy-mm-dd): 2000-01-01
Enter the end date (format: yyyy-mm-dd): 2010-01-01
Results saved to New_York_weather_data_2000-01-01_to_2010-01-01.csv
```

## Acknowledgements

- [Open-Meteo API](https://open-meteo.com/) for providing the weather data.
- [Geopy](https://geopy.readthedocs.io/) for geocoding city names.
- [Requests-Cache](https://requests-cache.readthedocs.io/) for caching API requests.
- [Retry Requests](https://github.com/invl/retry) for handling request retries.

## Notes
This code relies on the free Open-Meteo Historical Weather API and Weather Forecast API.
The program may hit the rate limit for API requests unless a commercial use license plan is purchased.

## Additional Information
For more details about the program, take a look at the Pitch Deck to learn more.

[![Check Style](https://github.com/kjx172/ClimaGraph/actions/workflows/style_checker.yaml/badge.svg)](https://github.com/kjx172/ClimaGraph/actions/workflows/style_checker.yaml)
