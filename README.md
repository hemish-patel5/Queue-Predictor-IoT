# Queue Time and Comfort Predictor


/Queue-Predictor-IoT
│
├── /hardware             # Member 1: Hardware & CV focus
│   ├── /drivers          # Python scripts for DHT22, CO2, Sound sensors [cite: 35, 36]
│   ├── /vision           # Pi Camera scripts for anonymous detection [cite: 37, 53]
│   └── calibration.py    # Camera/PIR sensor calibration logic [cite: 37]
│
├── /backend              # Member 3: Data & LLM focus
│   ├── /services         # LLM API integration (GPT/Claude) [cite: 30, 40]
│   ├── /logic            # Scripts to fuse sensor data into advisory messages [cite: 18, 41]
│   └── requirements.txt  # Python dependencies (OpenAI, OpenCV, etc.)
│
├── /frontend             # Member 2: Dashboard focus
│   ├── /public           # Static assets (icons, images)
│   ├── /src              # Web dashboard code (React/HTML/Tailwind) 
│   └── index.html        # Main dashboard entry point
│
├── /docs                 # Project Documentation
│   ├── /minutes          # Meeting minutes from weekly Zoom sessions [cite: 45, 51]
│   ├── /surveys          # User evaluation design and results [cite: 21, 39]
│   └── proposal.pdf      # The original project proposal [cite: 1]
│
├── .gitignore            # Files to exclude (e.g., .env with API keys)
└── README.md             # Project overview and setup instructions
