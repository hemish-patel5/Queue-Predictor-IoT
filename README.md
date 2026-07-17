
# Queue Time and Comfort Predictor
The Queue Time & Comfort Predictor is an IoT-based system that helps students and staff decide the best time to visit campus services (like IT helpdesks or cafes). It uses sensors and a camera to estimate queue length, wait time, and environmental comfort (e.g., noise, CO₂, temperature). This data is processed and turned into simple, real-time advisory messages—like when it’s a good time to go or when to avoid busy periods—via a dashboard or display.

<img width="1113" height="735" alt="iot2" src="https://github.com/user-attachments/assets/0285c8e4-ee54-4800-80a3-be6555aa1409" />
<img width="811" height="908" alt="iot3" src="https://github.com/user-attachments/assets/0fde1780-f8fb-491c-a149-1649cee5a88b" />
<img width="1299" height="557" alt="iot" src="https://github.com/user-attachments/assets/56b4a95d-1062-4880-979c-4bcfba480773" />
## Project Structure

```text
/Queue-Predictor-IoT
│
├── /hardware             # Member 1: Hardware & CV focus
│   ├── /drivers          # Python scripts for DHT22, CO2, Sound sensors
│   ├── /vision           # Pi Camera scripts for anonymous detection
│   └── calibration.py    # Camera/PIR sensor calibration logic
│
├── /backend              # Member 3: Data & LLM focus
│   ├── /services          # LLM API integration (GPT/Claude)
│   ├── /logic            # Scripts to fuse sensor data into advisory messages
│   └── requirements.txt  # Python dependencies (OpenAI, OpenCV, etc.)
│
├── /frontend             # Member 2: Dashboard focus
│   ├── /public           # Static assets (icons, images)
│   ├── /src              # Web dashboard code (React/HTML/Tailwind) 
│   └── index.html        # Main dashboard entry point
│
│
├── .gitignore            # Files to exclude (e.g., .env with API keys)
└── README.md             # Project overview and setup instructions
```

## Running the project

There are two helper scripts to start all components (drivers, backend and frontend):

- `run_all.sh` — Unix / WSL / Raspberry Pi
- `run_all.ps1` — Windows PowerShell (created to help Windows users)

Basic steps (Unix / macOS / Pi):

1. Create Python venv and install requirements (once):

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements-updated.txt
```

2. Create a `.env` file in the project root (copy `.env.example` if present) and set required keys (THINGSBOARD credentials, ACCESS_TOKEN, etc.).

3. Start everything:

```bash
chmod +x run_all.sh
./run_all.sh
```

On Windows (PowerShell):

1. Open PowerShell in the project root and run (this will create a venv and install dependencies if needed):

```powershell
.\run_all.ps1
```

2. Stop services:

```powershell
.\run_all.ps1 stop
```

Camera / YOLO prerequisites

- The vision pipeline uses `yolov8n.pt` (stored in project root) and requires OpenCV, ultralytics/YOLOv8 and a camera device (typically a USB webcam or Pi camera).
- For Raspberry Pi: install the Raspberry Pi camera drivers and Python packages (e.g., `opencv-python`, `paho-mqtt`, `ultralytics`). The Windows runner will skip launching the camera and prints instructions instead.
