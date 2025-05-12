import csv
import re
import os
from fastapi import FastAPI, HTTPException, status
from datetime import datetime
from dateutil.parser import parse
from contextlib import asynccontextmanager

# Optionally accept file name from env
restaurants_data_file = os.environ.get('RESTAURANTS_DATA_CSV', 'restaurants.csv')

# NOTE - I have not implemented a proper logger, that would be a good improvement to make

# More patterns to support can be added as needed
DAY_ALIASES = {
    "mon": 0, "monday": 0,
    "tue": 1, "tues": 1, "tuesday": 1,
    "wed": 2, "wednesday": 2,
    "thu": 3, "thurs": 3, "thursday": 3,
    "fri": 4, "friday": 4,
    "sat": 5, "saturday": 5,
    "sun": 6, "sunday": 6,
}


def weekday_to_int(day_str):
    '''
    Returns 0 for Mon, 1 for Tue =, etc.
    '''
    key = day_str.strip().lower()
    if key not in DAY_ALIASES:
        raise ValueError(f"Invalid weekday: {day_str}")
    return DAY_ALIASES[key]


def get_weekdays_ord(days_str: str): 
    '''
    Returns a list of ints representing weekdays 0-6 (Mon-Sun) included in days_str 
    that represents a day range 
    e.g. Mon-Wed -> [0 1 2]
    '''
    d_ranges = days_str.split(',')
    d_list = [] 
    for d in d_ranges:
        if '-' in d:
            dstart = weekday_to_int(d.split('-')[0])
            dend = weekday_to_int(d.split('-')[1])
            d_list.extend(range(dstart, dend+1))
        else:
            d_list.append(parse(d.strip()).weekday())
    return d_list


def is_valid_datetime(date_str):
    '''
    Check if string represents a valid date-time
    '''
    try:
        dt = parse(date_str)
        return True, dt
    except ValueError:
        return False, None


def parse_time_str(time_str: str):
    '''
    Parse string like 10:30 am or 11 pm
    '''
    if ":" not in time_str:
        return datetime.strptime(time_str, "%I %p").time()
    else: 
       return datetime.strptime(time_str, "%I:%M %p").time()


def is_time_within_interval(dt_obj, interval_str):
    """
    Checks if a datetime object falls within a time interval specified as a string.

    Args:
        dt_obj: datetime object to check.
        interval_str: String representing the time interval, e.g., "11:30 am - 11 pm".

    Returns:
        True if the datetime falls within the interval, False otherwise.
    """
    try:
        start_time_str, end_time_str = interval_str.split(" - ")
        start_time = parse_time_str(start_time_str)
        end_time = parse_time_str(end_time_str)
    except ValueError:
        raise ValueError("Invalid time interval format. Use 'HH:MM am/pm - HH:MM am/pm'")

    dt = dt_obj.time()

    if start_time <= end_time:
        return start_time <= dt <= end_time
    else: # Interval crosses midnight
        return dt >= start_time or dt <= end_time

restaurant_hours_data = {}

# Ingest and parse the CSV data
def load_restaurant_hours_data(datafile: str):
    # Note - We are assuming that the file is not too huge and can be ingested, parsed, and stored in memory on single server node
    # If this assumption does not hold, the solution would be different - e.g. ingesting to
    # a distributed key-value DB e.g. Minio / spark cluster / hadoop mapreduce 
    with open(datafile, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for r in reader:
            if "Restaurant Name" in r:
                continue
            r_name = r[0].strip('"').strip()
            r_hours = r[1].strip('"').strip()
            restaurant_hours_data.update({r_name: []})

            # Regex to capture open days-hours ranges   
            pattern = r"([A-Za-z,\s-]+?)\s+(\d{1,2}(?::\d{2})?\s*[ap]m\s*-\s*\d{1,2}(?::\d{2})?\s*[ap]m)"
            matches = re.findall(pattern, r_hours)
            for days, hours in matches:
                weekdays_ord = get_weekdays_ord(days.strip())
                restaurant_hours_data[r_name].append((weekdays_ord, hours))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the data and parse at startup 
    print("====Startup===")
    print("Loading restaurants hours data ...")
    load_restaurant_hours_data(datafile=restaurants_data_file)
    print(restaurant_hours_data)
    yield
    print("====Cleanup====")


app = FastAPI(lifespan=lifespan)

@app.get('/restaurants/{datetimeinput}')
async def get_restaurants(datetimeinput: str):
    is_valid, dt = is_valid_datetime(datetimeinput)
    if not is_valid:    
        return HTTPException(status.HTTP_400_BAD_REQUEST, "Must provide valid datetime string as param")  
    output = []
    # print(f"Input query is a {query_weekday} {dt.hour} H and {dt.minute} M")
    for restaurant in restaurant_hours_data:
        for (day_range, hr_range) in restaurant_hours_data[restaurant]:
            if dt.weekday() in day_range:
                # print(f"{restaurant} : {hr_range}")
                if is_time_within_interval(dt, hr_range):
                    output.append(restaurant)
    return output
