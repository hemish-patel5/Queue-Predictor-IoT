#!/usr/bin/env python3
"""
FastAPI Server for Queue Predictor IoT Dashboard
Integrates with ThingsBoard to fetch sensor data and expose endpoints for the frontend
Uses device ACCESS_TOKEN for HTTP API calls — no JWT required
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv
import logging
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from logic.sensor_fusion import SensorFusion
from services.LLM_advisory import AdvisoryService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(
    title="Queue Predictor IoT API",
    description="Backend API for Queue Time & Comfort Predictor Dashboard",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration ---
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN', '')
THINGSBOARD_HTTP_URL = os.getenv('THINGSBOARD_HTTP_URL', 'https://thingsboard.cloud')

# --- Services ---
sensor_fusion = SensorFusion()
advisory_service = AdvisoryService()

# --- Sensor keys published by the Pi ---
ALL_SENSOR_KEYS = [
    'people_in_frame',
    'queue_length',
    'gas_value',
    'gas_safe',
    'temperature',
    'humidity',
    'sound_value',
    'noise_level',
    'trigger_count',
    'motion_detected',
    'motion_count',
]

SENSOR_KEYS = {
    'camera': {
        'name': 'Camera (Vision)',
        'keys': ['people_in_frame', 'queue_length']
    },
    'co2': {
        'name': 'CO2 / Gas Sensor',
        'keys': ['gas_value', 'gas_safe']
    },
    'humiture': {
        'name': 'Temperature & Humidity',
        'keys': ['temperature', 'humidity']
    },
    'sound': {
        'name': 'Sound Sensor',
        'keys': ['sound_value', 'noise_level', 'trigger_count']
    },
    'pir': {
        'name': 'Motion Sensor (PIR)',
        'keys': ['motion_detected', 'motion_count']
    }
}

async def get_jwt_token() -> str:
    url = f"{THINGSBOARD_HTTP_URL}/api/auth/login"
    payload = {
        "username": os.getenv('THINGSBOARD_USERNAME'),
        "password": os.getenv('THINGSBOARD_PASSWORD')
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()['token']


async def fetch_telemetry(keys: list) -> dict:
    try:
        token = await get_jwt_token()
        device_id = os.getenv('THINGSBOARD_DEVICE_ID')

        url = f"{THINGSBOARD_HTTP_URL}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"
        params = {'keys': ','.join(keys)}
        headers = {'X-Authorization': f'Bearer {token}'}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Raw ThingsBoard response: {data}")

            # Extract latest value for each key
            parsed = {}
            for key, values in data.items():
                if values:
                    parsed[key] = values[0].get('value')

            logger.info(f"Parsed telemetry: {parsed}")
            return parsed

    except httpx.HTTPError as e:
        logger.warning(f"Failed to fetch telemetry: {e}")
        return {}
    
def safe_float(value, default=0.0):
    """Safely convert a value to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """Safely convert a value to int."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


# --- Routes ---

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Queue Predictor IoT API",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "thingsboard_url": THINGSBOARD_HTTP_URL,
        "token_configured": bool(ACCESS_TOKEN)
    }


@app.get("/api/v1/live-status")
async def get_live_status():
    """
    Get live dashboard status with all sensor data and advisory message.
    """
    try:
        telemetry = await fetch_telemetry(ALL_SENSOR_KEYS)

        # Extract values with safe defaults
        people_count    = safe_int(telemetry.get('people_in_frame', 0))
        gas_value       = safe_float(telemetry.get('gas_value', 0))
        gas_safe        = telemetry.get('gas_safe', True)
        temperature     = safe_float(telemetry.get('temperature', 20))
        humidity        = safe_float(telemetry.get('humidity', 50))
        sound_value     = safe_float(telemetry.get('sound_value', 0))
        noise_level     = telemetry.get('noise_level', 'quiet')
        motion_detected = telemetry.get('motion_detected', False)

        # Estimated wait time: 2 minutes per person
        estimated_wait_time = people_count * 2

        # Comfort metrics via sensor fusion
        comfort_data = sensor_fusion.calculate_comfort_metrics(
            temperature=temperature,
            humidity=humidity,
            co2_level=gas_value,
            noise_level=sound_value
        )

        # LLM advisory
        advisory_message = advisory_service.generate_advisory(
            people_count=people_count,
            co2_level=gas_value,
            temperature=temperature,
            humidity=humidity,
            noise_level=sound_value,
            comfort_score=comfort_data.get('comfort_score', 0)
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "live_status": {
                "people_count": people_count,
                "estimated_wait_time": estimated_wait_time,
                "advisory_message": advisory_message,
                "motion_detected": motion_detected
            },
            "environmental_metrics": {
                "temperature": round(temperature, 1),
                "humidity": round(humidity, 1),
                "gas_value": round(gas_value, 1),
                "gas_safe": gas_safe,
                "sound_value": round(sound_value, 1),
                "noise_level": noise_level,
                "air_quality_status": comfort_data.get('air_quality', 'unknown'),
                "comfort_status": comfort_data.get('thermal_comfort', 'unknown')
            },
            "comfort_data": comfort_data
        }

    except Exception as e:
        logger.error(f"Error fetching live status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sensor-health")
async def get_sensor_health():
    """
    Get health status of all connected sensors.
    A sensor is considered online if its key exists in the latest telemetry.
    """
    try:
        telemetry = await fetch_telemetry(ALL_SENSOR_KEYS)
        sensor_health = {}

        for sensor_key, sensor_info in SENSOR_KEYS.items():
            is_online = any(key in telemetry for key in sensor_info['keys'])
            sensor_health[sensor_key] = {
                "name": sensor_info['name'],
                "status": "online" if is_online else "offline",
                "last_update": datetime.now().isoformat() if is_online else None
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
    Get current comfort score and breakdown.
    """
    try:
        telemetry = await fetch_telemetry(['temperature', 'humidity', 'gas_value', 'sound_value'])

        temperature = safe_float(telemetry.get('temperature', 20))
        humidity    = safe_float(telemetry.get('humidity', 50))
        gas_value   = safe_float(telemetry.get('gas_value', 0))
        sound_value = safe_float(telemetry.get('sound_value', 0))

        comfort_data = sensor_fusion.calculate_comfort_metrics(
            temperature=temperature,
            humidity=humidity,
            co2_level=gas_value,
            noise_level=sound_value
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "comfort_data": comfort_data
        }

    except Exception as e:
        logger.error(f"Error calculating comfort score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/history")
async def get_history(hours: int = 6, limit: int = 100):
    """
    Placeholder for historical data endpoint.
    ThingsBoard historical telemetry requires JWT auth — implement if needed.
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "hours": hours,
        "message": "Historical data requires ThingsBoard JWT authentication. Use ThingsBoard dashboard for history.",
        "queue_history": [],
        "gas_history": [],
        "sound_history": [],
        "temperature_history": [],
        "humidity_history": []
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)