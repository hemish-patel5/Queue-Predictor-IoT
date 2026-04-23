# Queue Time and Comfort Predictor


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
