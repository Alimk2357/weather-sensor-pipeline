import json
import sys
from pydantic import BaseModel, Field, field_validator, ValidationError
import psycopg2
from elasticsearch import Elasticsearch

PG_CONN = psycopg2.connect(
    dbname="appdb", user="appuser", password="apppass", host="postgres-db", port="5432"
)
ES_CLIENT = Elasticsearch("http://elasticsearch:9200")

class WeatherData(BaseModel):
    sensor_id: str
    timestamp: str
    temperature: float = Field(..., description="Temperature (°C)")
    humidity: float = Field(..., ge=0, le=100, description="Humidity (%) must be in between 0 and 100.")
    wind_speed: float = Field(..., ge=0, description="Wind speed (km/h) cannot be negative.")
    rain_rate: float = Field(..., ge=0, description="Rain amount (mm/h) cannot be negative.")

    @field_validator('temperature')
    def check_temperature(cls, value):
        if value < -50 or value > 60:
            raise ValueError('Anomaly: Temperature must be in between -50°C and 60°C.')
        return value

    @field_validator('wind_speed')
    def check_wind_speed(cls, value):
        if value > 150:
            raise ValueError('Anomaly: Wind speed cannot exceed 150 km/h.')
        return value

def process_data(raw_json_str):
    data_list = json.loads(raw_json_str)

    cursor = PG_CONN.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_data (
            id SERIAL PRIMARY KEY,
            sensor_id VARCHAR(50),
            timestamp TIMESTAMP,
            temperature FLOAT,
            humidity FLOAT,
            wind_speed FLOAT,
            rain_rate FLOAT
        );
    """)
    PG_CONN.commit()

    for raw_dict in data_list:
        try:
            validated_data = WeatherData(**raw_dict)

            # If WeatherData does not throw exception, the data is valid
            # it can go to PostgreSQL
            cursor.execute("""
                INSERT INTO weather_data (sensor_id, timestamp, temperature, humidity, wind_speed, rain_rate)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                validated_data.sensor_id, validated_data.timestamp,
                validated_data.temperature, validated_data.humidity,
                validated_data.wind_speed, validated_data.rain_rate
            ))
            PG_CONN.commit()
            
        except ValidationError as e:
            # Exception is catched, data goes to Elasticsearch
            error_result = {
                "status": "invalid",
                "error_details": json.loads(e.json()),
                "original_data": raw_dict
            }
            ES_CLIENT.index(index="pydantic-errors", document=error_result)

    cursor.close()

if __name__ == "__main__":
    # NiFi ExecuteStreamCommand processor reads the data from stdin.
    input_data = sys.stdin.read() # string as json
    if input_data.strip():
        process_data(input_data)