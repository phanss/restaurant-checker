FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

# Define environment variable
ENV RESTAURANTS_DATA_CSV 'restaurants.csv'

# Run app.py when the container launches
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
