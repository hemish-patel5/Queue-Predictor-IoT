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
from datetime import datetime, timezone
from dotenv import load_dotenv
import logging
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from logic.sensor_fusion import SensorFusion
from services.LLM_advisory import AdvisoryService
load_dotenv()

# logging: enable debug when API_DEBUG=1 in environment
log_level = logging.DEBUG if os.getenv('API_DEBUG', '0') == '1' else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Queue Predictor IoT API",
    description="Backend API for Queue Time & Comfort Predictor Dashboard",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://queue-predictor-iot.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration ---
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN', '')
THINGSBOARD_HTTP_URL = os.getenv('THINGSBOARD_HTTP_URL', 'https://thingsboard.cloud')

# How old a ThingsBoard timestamp can be before a sensor is considered offline.
# Set this to ~2x your Pi's publish interval so one missed publish doesn't flip it.
OFFLINE_GRACE_SECONDS = int(os.getenv('SENSOR_OFFLINE_GRACE_SECONDS', '90'))

# --- Services ---
sensor_fusion = SensorFusion()
advisory_service = AdvisoryService()

# In-memory PIR live counters (ephemeral, reset on server restart)
PIR_LIVE = {
    'last_event_ts': 0,        # ms timestamp of last processed event
    'entry_count': 0,          # recent entry events (since last activity or reset)
    'exit_count': 0,           # recent exit events
    'current_occupancy': None, # inferred occupancy tracked by PIR events
    'last_activity_ms': 0,
}

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
    # PIR: motion and directional counts
    # PIR now publishes only these two keys
    'event',
    'occupancy',
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
        # PIR publishes only 'event' (per-event string) and 'occupancy' (current count)
        'keys': ['event', 'occupancy']
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

        logger.info(f"Fetching telemetry for device_id={device_id} token_present={bool(token)}")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"ThingsBoard request: GET {url} params={params} status={response.status_code}")
            if not data:
                logger.warning(f"ThingsBoard returned empty timeseries for keys={params.get('keys')}. Response text: {response.text}")
            logger.info(f"Raw ThingsBoard response: {data}")

            def parse_ts_to_ms(raw_ts):
                if raw_ts is None:
                    return None
                if isinstance(raw_ts, (int, float)):
                    ts_int = int(raw_ts)
                else:
                    raw_s = str(raw_ts).strip()
                    if raw_s.isdigit():
                        try:
                            ts_int = int(raw_s)
                        except Exception:
                            return None
                    else:
                        try:
                            dt = datetime.fromisoformat(raw_s)
                            ts_int = int(dt.timestamp() * 1000)
                        except Exception:
                            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S'):
                                try:
                                    dt = datetime.strptime(raw_s, fmt)
                                    ts_int = int(dt.timestamp() * 1000)
                                    break
                                except Exception:
                                    ts_int = None
                            if ts_int is None:
                                return None
                if ts_int is not None and ts_int < 1_000_000_000_000:
                    ts_int = ts_int * 1000
                return ts_int

            parsed = {}
            for key, values in data.items():
                if not values:
                    continue
                latest_item = None
                latest_ts = -1
                for item in values:
                    raw_ts = item.get('ts')
                    ts_candidate = parse_ts_to_ms(raw_ts)
                    if ts_candidate is None:
                        ts_candidate = 0
                    if ts_candidate > latest_ts:
                        latest_ts = ts_candidate
                        latest_item = item
                if latest_item is not None:
                    parsed[key] = {
                        'value': latest_item.get('value'),
                        'ts': parse_ts_to_ms(latest_item.get('ts'))
                    }

            for req_key in keys:
                if req_key not in parsed:
                    parsed[req_key] = {'value': None, 'ts': None}

            logger.info(f"Parsed telemetry: {parsed}")
            return parsed

    except httpx.HTTPError as e:
        logger.warning(f"Failed to fetch telemetry: {e}")
        return {}


def safe_float(value, default=0.0):
    try:
        if isinstance(value, dict):
            v = value.get('value')
        else:
            v = value
        return float(v)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    try:
        if isinstance(value, dict):
            v = value.get('value')
        else:
            v = value
        return int(v)
    except (ValueError, TypeError):
        return default


def is_recent(entry, max_age_seconds=300):
    if entry is None:
        return False
    if isinstance(entry, dict):
        ts = entry.get('ts')
        if not ts:
            return True
        try:
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            age_ms = now_ms - int(ts)
            return age_ms <= (max_age_seconds * 1000)
        except Exception:
            return True
    return True


def format_iso_utc(ts_ms: int) -> str:
    """Convert a millisecond UTC timestamp to an ISO-8601 string with 24hr time."""
    return datetime.utcfromtimestamp(ts_ms / 1000).strftime('%Y-%m-%dT%H:%M:%S') + 'Z'


# --- Routes ---

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "Queue Predictor IoT API",
        "timestamp": format_iso_utc(int(datetime.now(timezone.utc).timestamp() * 1000))
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
    try:
        telemetry = await fetch_telemetry(ALL_SENSOR_KEYS)
        logger.debug(f"Telemetry received for sensor-health: {telemetry}")

        # Use camera people_in_frame as the authoritative people count.
        # PIR is currently unavailable so ignore entry/exit counters.
        people_count = safe_int(telemetry.get('people_in_frame', 0))
        gas_value       = safe_float(telemetry.get('gas_value', 0))
        gas_safe        = telemetry.get('gas_safe', True)
        temperature     = safe_float(telemetry.get('temperature', 20))
        humidity        = safe_float(telemetry.get('humidity', 50))
        sound_value     = safe_float(telemetry.get('sound_value', 0))
        noise_level     = telemetry.get('noise_level', 'quiet')
        motion_detected = telemetry.get('motion_detected', False)

        estimated_wait_time = people_count * 2

        comfort_data = sensor_fusion.calculate_comfort_metrics(
            temperature=temperature,
            humidity=humidity,
            co2_level=gas_value,
            noise_level=sound_value
        )

        advisory_message = advisory_service.generate_advisory(
            people_count=people_count,
            co2_level=gas_value,
            temperature=temperature,
            humidity=humidity,
            noise_level=sound_value,
            comfort_score=comfort_data.get('comfort_score', 0)
        )

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
<<<<<<< HEAD
        # Only fetch and process new events since last processed event TS.
        entry_count_recent = 0
        exit_count_recent = 0
        try:
            token = await get_jwt_token()
            device_id = os.getenv('THINGSBOARD_DEVICE_ID')
            url = f"{THINGSBOARD_HTTP_URL}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries"
            # Request event timeseries newer than the last processed ts
            params = {
                'keys': 'event',
                'startTs': PIR_LIVE['last_event_ts'] + 1,
                'endTs': now_ms,
                'limit': 100
            }
            headers = {'X-Authorization': f'Bearer {token}'}
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                event_data = resp.json()
                events = event_data.get('event', []) or []
                # Process events in chronological order
                events.sort(key=lambda i: int(i.get('ts') or 0))
                for item in events:
                    ts = item.get('ts')
                    if ts is None:
                        continue
                    try:
                        ts_int = int(ts)
                    except Exception:
                        continue
                    # normalize seconds->ms
                    if ts_int < 1_000_000_000_000:
                        ts_int = ts_int * 1000
                    if ts_int <= PIR_LIVE['last_event_ts']:
                        continue
                    v = item.get('value')
                    if not isinstance(v, str):
                        continue
                    vv = v.lower()
                    # Update live counters
                    if vv == 'entry':
                        PIR_LIVE['entry_count'] += 1
                        PIR_LIVE['current_occupancy'] = (PIR_LIVE['current_occupancy'] or 0) + 1
                        entry_count_recent += 1
                    elif vv == 'exit':
                        PIR_LIVE['exit_count'] += 1
                        PIR_LIVE['current_occupancy'] = max(0, (PIR_LIVE['current_occupancy'] or 0) - 1)
                        exit_count_recent += 1
                    PIR_LIVE['last_event_ts'] = ts_int
                    PIR_LIVE['last_activity_ms'] = now_ms
        except Exception:
            logger.debug('Failed to fetch new event timeseries for counts', exc_info=True)

        # Reset live counters after inactivity
        try:
            PIR_RESET_MS = int(os.getenv('PIR_RESET_MS', str(5 * 60 * 1000)))
            if PIR_LIVE['last_activity_ms'] and (now_ms - PIR_LIVE['last_activity_ms'] > PIR_RESET_MS):
                PIR_LIVE['entry_count'] = 0
                PIR_LIVE['exit_count'] = 0
                PIR_LIVE['current_occupancy'] = None
                PIR_LIVE['last_event_ts'] = 0
                PIR_LIVE['last_activity_ms'] = 0
        except Exception:
            pass
        return {
            "timestamp": format_iso_utc(now_ms),
            "live_status": {
                    "people_count": people_count,
                # Expose live-entry/exit counts accumulated since server start
                # and reset behavior is handled below based on inactivity.
                "entry_count": PIR_LIVE['entry_count'],
                "exit_count": PIR_LIVE['exit_count'],
                    "pir_occupancy": PIR_LIVE['current_occupancy'],
=======
        return {
            "timestamp": format_iso_utc(now_ms),
            "live_status": {
                "people_count": people_count,
>>>>>>> parent of 8c6d5c1 (Added pir entry and exit)
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
async def get_sensor_health(debug: bool = False):
    """
    Get health status of all connected sensors.
    A sensor is online only if its most recent ThingsBoard timestamp (with a
    non-null value) is within SENSOR_OFFLINE_GRACE_SECONDS of now (UTC).
    Keys with null values are ignored — ThingsBoard returns fake current
    timestamps for keys that have never had real data.
    """
    try:
        telemetry = await fetch_telemetry(ALL_SENSOR_KEYS)
        sensor_health = {}
        sensor_debug = {}

        FUTURE_ALLOW_MS = 30 * 1000
        MAX_ACCEPT_FUTURE_MS = int(os.getenv('THINGSBOARD_MAX_FUTURE_SECONDS', str(12 * 3600))) * 1000

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        for sensor_key, sensor_info in SENSOR_KEYS.items():
            # Find the most recent timestamp across all keys for this sensor,
            # but ONLY consider entries that have a real (non-null) value.
            latest_ts_ms = None
            latest_key = None
            for key in sensor_info['keys']:
                entry = telemetry.get(key)
                logger.debug(f"  [{sensor_key}] key={key} entry={entry}")

                if not isinstance(entry, dict):
                    continue

                # Skip null-value entries — ThingsBoard generates a current
                # timestamp for keys that have never received real data.
                if entry.get('value') is None:
                    logger.debug(f"    [{sensor_key}] key={key} has null value — skipping")
                    continue

                ts = entry.get('ts')
                if ts is None:
                    continue

                try:
                    ts_int = int(ts)
                except Exception:
                    continue

                # Normalize seconds -> ms
                if ts_int < 1_000_000_000_000:
                    ts_int = ts_int * 1000

                if latest_ts_ms is None or ts_int > latest_ts_ms:
                    latest_ts_ms = ts_int
                    latest_key = key

            is_online = False
            last_update = None
            stale_seconds = None
            ts_ms = None

            if latest_ts_ms is not None:
                ts_ms = latest_ts_ms

                # Clamp modest future skew down to now
                if ts_ms > now_ms + FUTURE_ALLOW_MS:
                    if ts_ms <= now_ms + MAX_ACCEPT_FUTURE_MS:
                        ts_ms = now_ms
                    else:
                        # Implausibly far in the future — treat as missing
                        ts_ms = None

            if ts_ms is not None:
                age_ms = now_ms - ts_ms
                stale_seconds = int(max(0, age_ms) / 1000)
                is_online = age_ms <= (OFFLINE_GRACE_SECONDS * 1000)
                last_update = format_iso_utc(ts_ms)
                logger.debug(
                    f"Sensor '{sensor_key}' ts={ts_ms} now={now_ms} "
                    f"age_s={stale_seconds} online={is_online} (grace={OFFLINE_GRACE_SECONDS}s)"
                )
            else:
                is_online = False
                logger.debug(f"Sensor '{sensor_key}' has no valid non-null timestamp — offline")

            sensor_debug[sensor_key] = {
                'latest_ts_ms': ts_ms,
                'latest_key': latest_key,
                'stale_seconds': stale_seconds,
                'is_online': is_online,
            }

            sensor_health[sensor_key] = {
                'name': sensor_info['name'],
                'status': 'online' if is_online else 'offline',
                'last_update': last_update,
                'stale_seconds': stale_seconds,
                'alert': not is_online,
                # expose the configured telemetry keys for the frontend
                'data_keys': sensor_info.get('keys', [])
            }

        response = {
            'timestamp': format_iso_utc(now_ms),
            'sensors': sensor_health
        }

        if debug:
            response['debug'] = {
                'telemetry': telemetry,
                'sensors_debug': sensor_debug,
                'offline_grace_seconds': OFFLINE_GRACE_SECONDS,
                'server_now_ms': now_ms,
            }

        return response

    except Exception as e:
        logger.error(f"Error fetching sensor health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/comfort-score")
async def get_comfort_score():
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
            "timestamp": format_iso_utc(int(datetime.now(timezone.utc).timestamp() * 1000)),
            "comfort_data": comfort_data
        }

    except Exception as e:
        logger.error(f"Error calculating comfort score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/history")
async def get_history(hours: int = 6, limit: int = None):
    try:
        token = await get_jwt_token()
        device_id = os.getenv('THINGSBOARD_DEVICE_ID')

        now_utc = datetime.now(timezone.utc)
        end_ts = int(now_utc.timestamp() * 1000)
        start_ts = end_ts - int(hours * 3600 * 1000)

        # Choose aggregation based on time window
        if hours <= 1:
            agg = "NONE"
            interval_ms = None
            fetch_limit = 500
        elif hours <= 6:
            agg = "AVG"
            interval_ms = 1 * 60 * 1000        
        elif hours <= 24:
            agg = "AVG"
            interval_ms = 5 * 60 * 1000        
        elif hours <= 72:
            agg = "AVG"
            interval_ms = 15 * 60 * 1000       
        else:
            agg = "AVG"
            interval_ms = 30 * 60 * 1000       

        if agg == "NONE":
            fetch_limit = 500
        else:
            fetch_limit = int((hours * 3600 * 1000) / interval_ms) + 10

        keys = [
            'people_in_frame',
            'queue_length',
            'gas_value',
            'sound_value',
            'temperature',
            'humidity'
        ]

        data = {}
        async with httpx.AsyncClient(timeout=15.0) as client:
            for key in keys:
                params = {
                    'keys': key,
                    'startTs': start_ts,
                    'endTs': end_ts,
                    'limit': fetch_limit,
                    'agg': agg,
                }
                if interval_ms:
                    params['interval'] = interval_ms

                headers = {'X-Authorization': f'Bearer {token}'}
                response = await client.get(
                    f"{THINGSBOARD_HTTP_URL}/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries",
                    params=params,
                    headers=headers
                )
                response.raise_for_status()
                key_data = response.json()
                data[key] = key_data.get(key, [])

        def normalize_hist(key):
            values = data.get(key, []) or []
            out = []
            for item in values:
                try:
                    out.append({
                        'ts': int(item.get('ts')),
                        'value': item.get('value')
                    })
                except Exception:
                    continue
            out.sort(key=lambda x: x['ts'])
            return out

        return {
            "timestamp": format_iso_utc(end_ts),
            "hours": hours,
            "queue_history": normalize_hist('people_in_frame'),
            "queue_length_history": normalize_hist('queue_length'),
            "gas_history": normalize_hist('gas_value'),
            "sound_history": normalize_hist('sound_value'),
            "temperature_history": normalize_hist('temperature'),
            "humidity_history": normalize_hist('humidity')
        }

    except httpx.HTTPError as e:
        logger.warning(f"Failed to fetch history: {e}")
        return {
            "timestamp": format_iso_utc(int(datetime.now(timezone.utc).timestamp() * 1000)),
            "hours": hours,
            "message": f"Failed to fetch history: {e}",
            "queue_history": [],
            "queue_length_history": [],
            "gas_history": [],
            "sound_history": [],
            "temperature_history": [],
            "humidity_history": []
        }
    except Exception as e:
        logger.error(f"Error in history endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
