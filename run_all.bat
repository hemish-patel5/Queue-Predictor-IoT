@echo off
echo Starting all drivers...
 
start "Humiture" python hardware/drivers/humiture_sensor.py
start "CO2"      python hardware/drivers/co2_sensor.py
start "Sound"    python hardware/drivers/sound_sensor.py
start "PIR"      python hardware/drivers/pir_sensor.py
start "Vision"   python hardware/vision/camera_logic.py
 
timeout /t 3 /nobreak >nul
 
start "Fusion"   python backend/logic/sensor_fusion.py
 
echo All drivers running. Close this window to keep them running.
pause
 