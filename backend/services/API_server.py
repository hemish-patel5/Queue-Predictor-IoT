#!/usr/bin/env python3
"""
FastAPI Server for Queue Predictor IoT Dashboard
Integrates with ThingsBoard to fetch sensor data and expose endpoints for the frontend
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os
import json
from datetime import datetime
from dotenv import load_dotenv
import logging

# Import custom modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from logic.sensor_fusion import SensorFusion
from services.LLM_advisory import AdvisoryService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Queue Predictor IoT API",
    description="Backend API for Queue Time & Comfort Predictor Dashboard",
    version="1.0.0"
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
THINGSBOARD_HOST = os.getenv('THINGSBOARD_HOST', 'localhost')
THINGSBOARD_PORT = os.getenv('THINGSBOARD_PORT', 8080)
DEVICE_ACCESS_TOKEN = os.getenv('ACCESS_TOKEN', '')
THINGSBOARD_URL = f"http://{THINGSBOARD_HOST}:{THINGSBOARD_PORT}"

# Initialize services
sensor_fusion = SensorFusion()
advisory_service = AdvisoryService()

# Single Raspberry Pi device with all sensors
# All sensors connected to one Pi, all data published with single ACCESS_TOKEN
SENSOR_KEYS = {
    'camera': {
        'name': 'Camera (Vision)',
        'keys': ['people_in_frame', 'queue_length']
    },
    'co2': {
        'name': 'CO2 Sensor',
        'keys': ['gas_value', 'co2_ppm', 'gas_safe']
    },
    'humiture': {
        'name': 'Temperature & Humidity',
        'keys': ['temperature', 'humidity']
    },
    'sound': {
        'name': 'Sound Sensor',
        'keys': ['sound_value', 'noise_db', 'noise_level', 'trigger_count']
    },
    'pir': {
        'name': 'Motion Sensor (PIR)',
        'keys': ['motion_detected', 'motion_count']
    }
}


async def fetch_telemetry(device_token: str, keys: list):
    """
    Fetch telemetry data from ThingsBoard for a specific device
    """
    try:
        # Endpoint for latest telemetry
        url = f"{THINGSBOARD_URL}/api/v1/{device_token}/latest/telemetry"
        params = {'keys': ','.join(keys)}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.warning(f"Failed to fetch telemetry: {e}")
        return {}


async def fetch_device_telemetry(device_id: str, keys: list, limit: int = 100):
    """
    Fetch historical telemetry data from ThingsBoard
    """
    try:
        url = f"{THINGSBOARD_URL}/api/v1/{DEVICE_ACCESS_TOKEN}/timeseries/{device_id}"
        params = {
            'keys': ','.join(keys),
            'limit': limit,
            'desc': True  # Descending order (most recent first)
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.warning(f"Failed to fetch device telemetry: {e}")
        return {}


async def fetch_attribute(device_token: str, attribute_name: str):
    """
    Fetch device attribute from ThingsBoard
    """
    try:
        url = f"{THINGSBOARD_URL}/api/v1/{device_token}/attributes"
        params = {'clientKeys': attribute_name}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.warning(f"Failed to fetch attribute: {e}")
        return {}


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Queue Predictor IoT API",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/live-status")
async def get_live_status():
    """
    Get live dashboard status with all sensor data and advisory message
    """
    try:
        # Fetch latest telemetry from all sensors (single device with single token)
        all_telemetry = await fetch_telemetry(
            DEVICE_ACCESS_TOKEN,
            ['people_in_frame', 'gas_value', 'gas_safe', 'temperature', 'humidity', 
             'sound_value', 'noise_level', 'co2_ppm', 'noise_db', 'motion_detected']
        )

        # Extract values from telemetry with fallback defaults
        # Camera data
        people_count = all_telemetry.get('people_in_frame', [{}])[0].get('value', 0) if all_telemetry.get('people_in_frame') else 0
        
        # CO2 data - use both gas_value and co2_ppm if available
        co2_level = all_telemetry.get('co2_ppm', [{}])[0].get('value', 400) if all_telemetry.get('co2_ppm') else 400
        if not co2_level or co2_level == 400:
            gas_val = all_telemetry.get('gas_value', [{}])[0].get('value', 0) if all_telemetry.get('gas_value') else 0
            # Convert gas sensor raw value to approximate ppm if needed
            co2_level = gas_val if gas_val > 100 else 400
        
        # Temperature and Humidity data
        temperature = all_telemetry.get('temperature', [{}])[0].get('value', 20) if all_telemetry.get('temperature') else 20
        humidity = all_telemetry.get('humidity', [{}])[0].get('value', 50) if all_telemetry.get('humidity') else 50
        
        # Sound data - use both sound_value and noise_db if available
        noise_db = all_telemetry.get('noise_db', [{}])[0].get('value', 40) if all_telemetry.get('noise_db') else 40
        if not noise_db or noise_db == 40:
            sound_val = all_telemetry.get('sound_value', [{}])[0].get('value', 0) if all_telemetry.get('sound_value') else 0
            # Convert sound sensor value to approximate dB
            noise_db = sound_val if sound_val > 20 else 40

        # Convert people_count to integer
        try:
            people_count = int(people_count)
        except (ValueError, TypeError):
            people_count = 0

        # Calculate estimated wait time (2 minutes per person)
        estimated_wait_time = people_count * 2

        # Use sensor fusion to calculate comfort metrics
        comfort_data = sensor_fusion.calculate_comfort_metrics(
            temperature=temperature,
            humidity=humidity,
            co2_level=co2_level,
            noise_level=noise_db
        )

        # Get LLM advisory message
        advisory_message = advisory_service.generate_advisory(
            people_count=people_count,
            co2_level=co2_level,
            temperature=temperature,
            humidity=humidity,
            noise_level=noise_db,
            comfort_score=comfort_data['comfort_score']
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "live_status": {
                "people_count": people_count,
                "estimated_wait_time": estimated_wait_time,  # in minutes
                "advisory_message": advisory_message
            },
            "environmental_metrics": {
                "temperature": round(float(temperature), 1),
                "humidity": round(float(humidity), 1),
                "co2_ppm": round(float(co2_level), 0),
                "noise_db": round(float(noise_db), 1),
                "air_quality_status": comfort_data['air_quality'],
                "comfort_status": comfort_data['thermal_comfort']
            },
            "comfort_data": comfort_data
        }

    except Exception as e:
        logger.error(f"Error fetching live status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/history")
async def get_history(hours: int = 6, limit: int = 100):
    """
    Get historical data for trends visualization
    """
    try:
        # This endpoint would need device IDs from ThingsBoard
        # For now, returning a template response
        return {
            "timestamp": datetime.now().isoformat(),
            "hours": hours,
            "queue_history": [],
            "co2_history": [],
            "sound_history": [],
            "temperature_history": [],
            "humidity_history": []
        }
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sensor-health")
async def get_sensor_health():
    """
    Get health status of all connected sensors
    """
    try:
        # Try to fetch data from all sensor keys to determine if they're online
        sensor_health = {}
        
        # Single device publishes all sensors with one token
        all_telemetry = await fetch_telemetry(
            DEVICE_ACCESS_TOKEN,
            list(set([key for sensor in SENSOR_KEYS.values() for key in sensor['keys']]))
        )

        for sensor_key, sensor_info in SENSOR_KEYS.items():
            try:
                # Check if any of this sensor's keys have recent data
                is_online = False
                for key in sensor_info['keys']:
                    if key in all_telemetry and all_telemetry[key]:
                        is_online = True
                        break
                
                sensor_health[sensor_key] = {
                    "name": sensor_info['name'],
                    "status": "online" if is_online else "offline",
                    "last_update": datetime.now().isoformat() if is_online else None
                }
            except Exception as e:
                sensor_health[sensor_key] = {
                    "name": sensor_info['name'],
                    "status": "offline",
                    "error": str(e)
                }

        return {
            "timestamp": datetime.now().isoformat(),
            "sensors": sensor_health
        }

    except Exception as e:
        logger.error(f"Error fetching sensor health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/comfort-score")
async def get_comfort_score():
    """
    Get current comfort score and breakdown
    """
    try:
        # Fetch all sensor data from single device
        all_telemetry = await fetch_telemetry(
            DEVICE_ACCESS_TOKEN,
            ['temperature', 'humidity', 'co2_ppm', 'gas_value', 'noise_db', 'sound_value']
        )

        temperature = all_telemetry.get('temperature', [{}])[0].get('value', 20) if all_telemetry.get('temperature') else 20
        humidity = all_telemetry.get('humidity', [{}])[0].get('value', 50) if all_telemetry.get('humidity') else 50
        
        co2_level = all_telemetry.get('co2_ppm', [{}])[0].get('value', 400) if all_telemetry.get('co2_ppm') else 400
        if not co2_level or co2_level == 400:
            gas_val = all_telemetry.get('gas_value', [{}])[0].get('value', 0) if all_telemetry.get('gas_value') else 0
            co2_level = gas_val if gas_val > 100 else 400
        
        noise_level = all_telemetry.get('noise_db', [{}])[0].get('value', 40) if all_telemetry.get('noise_db') else 40
        if not noise_level or noise_level == 40:
            sound_val = all_telemetry.get('sound_value', [{}])[0].get('value', 0) if all_telemetry.get('sound_value') else 0
            noise_level = sound_val if sound_val > 20 else 40

        comfort_data = sensor_fusion.calculate_comfort_metrics(
            temperature=temperature,
            humidity=humidity,
            co2_level=co2_level,
            noise_level=noise_level
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "comfort_data": comfort_data
        }

    except Exception as e:
        logger.error(f"Error calculating comfort score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "thingsboard_url": THINGSBOARD_URL
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
