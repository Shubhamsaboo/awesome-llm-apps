from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field

# Initialize the FirecrawlApp with your API key
app = FirecrawlApp(api_key='')

class ExtractSchema(BaseModel):
    aqi: float = Field(description="Air Quality Index")
    temperature: float = Field(description="Temperature in degrees Celsius")
    humidity: float = Field(description="Humidity percentage")
    wind_speed: float = Field(description="Wind speed in kilometers per hour")
    pm25: float = Field(description="Particulate Matter 2.5 micrometers")
    pm10: float = Field(description="Particulate Matter 10 micrometers")
    co: float = Field(description="Carbon Monoxide level")

data = app.extract([
  'https://www.aqi.in/dashboard/india/andhra-pradesh/kakinada/*'
], {
    'prompt': 'Extract the AQI, temperature, humidity, wind speed, PM2.5, PM10, and CO levels from the page.',
    'schema': ExtractSchema.model_json_schema(),
})
print(data)