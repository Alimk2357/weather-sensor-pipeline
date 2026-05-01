import datetime
from typing import List, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Deterministic Weather Sensor API")

# Normally, FastAPI checks the data types via Pydantic at the background 
# and throws an error if there is a mismatch.
# To prevent this (to observe the Pydantic's role in the pipeline), some of
# the class members' type is made Any.
class WeatherSensorData(BaseModel):
    sensor_id: str
    timestamp: str
    temperature: Any 
    humidity: Any
    wind_speed: Any
    rain_rate: Any

@app.get("/weather/{sensor_id}", response_model=List[WeatherSensorData])
def get_weather_data(sensor_id: str):
    if not sensor_id.isalnum():
        raise HTTPException(status_code=400, detail="Invalid Sensor ID format")

    now = datetime.datetime.now()
    
    # 7 valid, 3 invalid pre-determined data (to ensure the output is deterministic)
    batch = [
        # Valid data, goes to PostgreSQL
        {"temp": 22.5, "hum": 45.0, "wind": 15.2, "rain": 0.0},
        {"temp": 18.0, "hum": 60.5, "wind": 25.0, "rain": 5.5},
        {"temp": 30.1, "hum": 35.0, "wind": 10.0, "rain": 0.0},
        {"temp": -5.5, "hum": 80.0, "wind": 45.5, "rain": 12.0},
        {"temp": 15.0, "hum": 55.5, "wind": 5.0,  "rain": 2.2},
        {"temp": 42.0, "hum": 20.0, "wind": 30.0, "rain": 0.0},
        {"temp": 10.5, "hum": 90.0, "wind": 60.0, "rain": 25.4},
        
        # Invalid data, goes to Elasticsearch
        # ERROR 1: type_error (temp is string, not float)
        {"temp": "yirmi beş", "hum": 50.0, "wind": 20.0, "rain": 0.0},
        # ERROR: value_error (temp > 60)
        {"temp": 85.0, "hum": 10.0, "wind": 5.0, "rain": 0.0},
        # ERROR 3: value_error (wind > 150)
        {"temp": 20.0, "hum": 40.0, "wind": 185.0, "rain": 0.0}
    ]

    response_data = []
    
    for i, data in enumerate(batch):
        time_offset = now - datetime.timedelta(minutes=i)
        
        record = WeatherSensorData(
            sensor_id=sensor_id,
            timestamp=time_offset.isoformat(),
            temperature=data["temp"],
            humidity=data["hum"],
            wind_speed=data["wind"],
            rain_rate=data["rain"]
        )
        response_data.append(record)
    
    return response_data

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)