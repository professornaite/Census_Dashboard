import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv

# Load API key from environment variable
#load_dotenv(dotenv_path='key.env')
#api_key = os.getenv('7185e8647a384134acea2bc035b844fa')
api_key = '7185e8647a384134acea2bc035b844fa'
# Define Census API parameters
BASE_URL = "https://api.census.gov/data/"
START_YEAR = 2009  # ACS5 data is available from 2009 onwards
END_YEAR = 2024
SURVEY = "acs/acs5"

# Define variables to fetch
VARIABLES = [
    "B01003_001E",  # Total population
    "B02001_002E",  # White alone
    "B02001_003E",  # Black or African American alone
    "B02001_004E",  # American Indian and Alaska Native alone
    "B02001_005E",  # Asian alone
    "B02001_006E",  # Native Hawaiian and Other Pacific Islander alone
    "B02001_007E",  # Some other race alone
    "B02001_008E",  # Two or more races
    "B02001_009E",  # Two races including Some other race
    "B02001_010E",  # Two races excluding Some other race, and three or more races
]

VALID_YEARS = []

# Check API availability for years
def check_available_years():
    global VALID_YEARS
    for year in range(START_YEAR, END_YEAR + 1):
        url = f"{BASE_URL}{year}/{SURVEY}/variables.json"
        response = requests.get(url)
        if response.status_code == 200:
            VALID_YEARS.append(year)
        time.sleep(0.5)  # Avoid rate limit
    print(f"Valid years for ACS5 data: {VALID_YEARS}")


def fetch_census_data(year):
    variables_str = ",".join(VARIABLES)  # Ensure proper formatting
    url = f'{BASE_URL}{year}/{SURVEY}?get=NAME,{variables_str}&for=state:*&key={api_key}'
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data[1:], columns=data[0])
        df["YEAR"] = year
        return df
    except requests.exceptions.RequestException as e:
        print(f"Skipping year {year}: {e}")
        return None

def collect_all_years_data():
    check_available_years()
    all_data = []
    
    for year in VALID_YEARS:
        print(f"Processing year {year}...")
        year_data = fetch_census_data(year)
        if year_data is not None:
            all_data.append(year_data)
        time.sleep(1)  # Prevent hitting API rate limits
    
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df.to_csv("census_acs5_all_states_2009_present.csv", index=False) # save file here
        print("Data fetching complete. File saved as 'census_acs5_all_states_2009_present.csv'")
    else:
        print("No data collected.")

# Run the script
collect_all_years_data()
