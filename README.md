# restaurant-checker

A FastAPI application which serves an API with an endpoint which takes a single parameter, a datetime string, and returns a list of restaurant names which are open on that date and time. The restaurant hours data can be supplied in a CSV file specified by environment var RESTAURANTS_DATA_CSV.

To run the API service --

```
pip install -r requirements.txt
uvicorn app:app --reload
```

To test the API endoint -- 

```
curl http://127.0.0.1:8000/restaurants/2025-05-19%2022:14
```
