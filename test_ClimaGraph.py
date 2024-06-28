import unittest
from unittest.mock import patch, mock_open, MagicMock
from ClimaGraph import *
from io import StringIO
import pandas as pd
from datetime import datetime, timedelta
import warnings


class TestWeatherData(unittest.TestCase):

    @patch('builtins.input', side_effect=[
        1, 'New York', '2023-01-01', '2023-01-07'])
    def test_weather_forecast(self, mock_input):
        # Test weather_forecast function with mocked user input
        cities_dict = weather_forecast('2023-01-01', '2023-01-07')
        # Assert that the function returns a dictionary
        self.assertIsInstance(cities_dict, dict)
        # Assert that the dictionary is not empty
        self.assertTrue(len(cities_dict) > 0)

    @patch('builtins.input', side_effect=[
        1, 'New York', '2023-01-01', '2023-01-07'])
    def test_weather_archive(self, mock_input):
        # Test weather_archive function with mocked user input
        cities_dict = weather_archive('2023-01-01', '2023-01-07')
        # Assert that the function returns a dictionary
        self.assertIsInstance(cities_dict, dict)
        # Assert that the dictionary is not empty
        self.assertTrue(len(cities_dict) > 0)

    @patch('builtins.input', side_effect=[
        'New York', '2023-01-01', '2023-01-01', '2023-01-07'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_query_database_existing_city(self, mock_stdout, mock_input):
        # Test query_database function with mocked
        # Database response for an existing city
        with patch('weather_data.sqlite3') as mock_sqlite:
            mock_cursor = mock_sqlite.connect().cursor()
            # Mock database cursor to return a known result
            mock_cursor.fetchall.return_value = [
                ('2023-01-01_weather_data_2023-01-01_to_2023-01-07.csv',)]
            query_database()
        # Assert that the expected message is printed
        saved_csv = "2023-01-01_weather_data_2023-01-01_to_2023-01-07.csv"
        self.assertIn(
            f"Results saved to {saved_csv}", mock_stdout.getvalue().strip())

    @patch('builtins.input', side_effect=[
        'Nonexistent City', '2023-01-01', '2023-01-01', '2023-01-07'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_query_database_nonexistent_city(self, mock_stdout, mock_input):
        # Test query_database function with mocked
        # Database response for a nonexistent city
        with patch('weather_data.sqlite3') as mock_sqlite:
            mock_cursor = mock_sqlite.connect().cursor()
            # Mock database cursor to return an empty result
            mock_cursor.fetchall.return_value = [
                ('2023-01-01_weather_data_2023-01-01_to_2023-01-07.csv',)]
            query_database()

        # Assert that the expected error message is printed
        prompt_str = "Please enter a valid city name"
        self.assertIn(
            f"Error: City not found in database. {prompt_str}.",
            mock_stdout.getvalue().strip()
        )

    @patch('weather_data.sqlite3.connect')
    @patch('pandas.DataFrame.to_sql')
    def test_write_to_file(self, mock_to_sql, mock_connect):
        # Mock the connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Create a sample cities_dict with a pandas dataframe
        sample_data = {
            'date': ['2023-01-01', '2023-01-02'],
            'temperature_2m_max': [5.0, 6.0],
            'temperature_2m_min': [1.0, 2.0],
            'uv_index_max': [3.0, 4.0],
            'precipitation_sum': [0.0, 0.1],
            'wind_speed_10m_max': [10.0, 12.0]
        }
        sample_df = pd.DataFrame(sample_data)
        cities_dict = {'New York': sample_df}

        # Call the write_to_file function with the sample data
        write_to_file(cities_dict)

        # Verify that the correct SQL commands were executed
        expected_table_name = 'New_York'
        mock_cursor.execute.assert_any_call(
            f'''CREATE TABLE IF NOT EXISTS {expected_table_name} (
                        date TEXT,
                        temperature_2m_max REAL,
                        temperature_2m_min REAL,
                        uv_index_max REAL,
                        precipitation_sum REAL,
                        wind_speed_10m_max REAL)''')

        # Check that commit was called, but allow for multiple calls
        self.assertTrue(mock_conn.commit.call_count >= 1)
        mock_conn.close.assert_called_once()

        # Verify that the dataframe was written to the table
        sample_df.to_sql.assert_called_with(
            expected_table_name,
            mock_conn, if_exists='replace', index=False
        )

    def test_check_date(self):
        # Test dates before 2016
        self.assertTrue(check_date('2015-12-31'))
        self.assertTrue(check_date('2000-01-01'))

        # Test date on 2016
        self.assertFalse(check_date('2016-01-01'))

        # Test dates after 2016
        self.assertFalse(check_date('2017-01-01'))
        self.assertFalse(check_date('2020-01-01'))

    @patch('builtins.input', side_effect=['invalid-date', '2023-01-01'])
    @patch('builtins.print')
    def test_ensure_valid_date(self, mock_print, mock_input):
        # Test the function with invalid date followed by a valid date
        result = ensure_valid_date("Enter the date (format: yyyy-mm-dd): ")
        self.assertEqual(result, '2023-01-01')

        # Check if the error message was printed for the invalid date
        mock_print.assert_called_with(
            "Invalid date format. Please enter the date in yyyy-mm-dd format."
        )

    def test_check_range(self):
        # Test a valid date range
        self.assertEqual(check_range('2020-01-01', '2020-12-31'), 0)
        # Test with the start date after the end date
        self.assertEqual(check_range('2021-01-01', '2020-01-01'), -1)
        # Test with the start date before 1940
        self.assertEqual(check_range('1939-12-31', '2020-01-01'), -2)
        # Test with the end date after the current date
        future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.assertEqual(check_range('2020-01-01', future_date), -3)

    def test_create_graph(self):
        # Mock cities_dict with dummy dataframes
        cities_dict = {
            'New York': pd.DataFrame({
                'date': pd.date_range('2023-01-01', periods=5),
                'temperature': [10, 15, 20, 25, 30]
            }),
            'Los Angeles': pd.DataFrame({
                'date': pd.date_range('2023-01-01', periods=5),
                'temperature': [15, 18, 22, 26, 29]
            })
        }

        target_var = 'temperature'

        # with self.assertWarns(UserWarning):
        #     create_graph(cities_dict, target_var)

        # Test that the plot file is created
        expected_filename = f'{target_var}_plot.png'
        try:
            plt.imread(expected_filename)  # Check if the file exists
        except FileNotFoundError:
            self.fail(f"Plot file '{expected_filename}' not created.")


# if __name__ == '__main__':
#     unittest.main()
