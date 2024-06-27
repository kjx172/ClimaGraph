import unittest
from unittest.mock import patch, mock_open
from weather_data import *
from io import StringIO

class TestWeatherData(unittest.TestCase):

    @patch('builtins.input', side_effect=['New York', '2023-01-01', '2023-01-07'])
    def test_weather_forecast(self, mock_input):
        # Test weather_forecast function with mocked user input
        cities_dict = weather_forecast('2023-01-01', '2023-01-07')
        # Assert that the function returns a dictionary
        self.assertIsInstance(cities_dict, dict)
        # Assert that the dictionary is not empty
        self.assertTrue(len(cities_dict) > 0)

    @patch('builtins.input', side_effect=['New York', '2023-01-01', '2023-01-07'])
    def test_weather_archive(self, mock_input):
        # Test weather_archive function with mocked user input
        cities_dict = weather_archive('2023-01-01', '2023-01-07')
        # Assert that the function returns a dictionary
        self.assertIsInstance(cities_dict, dict)
        # Assert that the dictionary is not empty
        self.assertTrue(len(cities_dict) > 0)

    @patch('builtins.input', side_effect=['New York'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_query_database_existing_city(self, mock_stdout, mock_input):
        # Test query_database function with mocked database response for an existing city
        with patch('weather_data.sqlite3') as mock_sqlite:
            mock_cursor = mock_sqlite.connect().cursor()
            # Mock database cursor to return a known result
            mock_cursor.fetchall.return_value = [('New_York_weather_data_2023-01-01_to_2023-01-07.csv',)]
            query_database()

        # Assert that the expected message is printed
        self.assertIn("Results saved to New_York_weather_data_2023-01-01_to_2023-01-07.csv", mock_stdout.getvalue().strip())

    @patch('builtins.input', side_effect=['Nonexistent City'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_query_database_nonexistent_city(self, mock_stdout, mock_input):
        # Test query_database function with mocked database response for a nonexistent city
        with patch('weather_data.sqlite3') as mock_sqlite:
            mock_cursor = mock_sqlite.connect().cursor()
            # Mock database cursor to return an empty result
            mock_cursor.fetchall.return_value = []
            query_database()

        # Assert that the expected error message is printed
        self.assertIn("Error: City not found in database. Please enter a valid city name.", mock_stdout.getvalue().strip())

    # Add more tests as needed

# if __name__ == '__main__':
#     unittest.main()

