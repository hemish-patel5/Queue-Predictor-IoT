#!/usr/bin/env python3
"""
Sensor Fusion Logic
Combines multiple sensor readings to calculate comfort scores and environmental insights
"""

import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class SensorFusion:
    """
    Fuses data from multiple sensors to provide comfort metrics and insights
    """

    def __init__(self):
        # Comfort thresholds
        self.TEMP_OPTIMAL_MIN = 20  # °C
        self.TEMP_OPTIMAL_MAX = 24  # °C
        self.HUMIDITY_OPTIMAL_MIN = 40  # %
        self.HUMIDITY_OPTIMAL_MAX = 60  # %
        self.CO2_SAFE = 1000  # ppm
        self.CO2_WARNING = 1500  # ppm
        self.NOISE_QUIET = 50  # dB
        self.NOISE_MODERATE = 65  # dB
        self.NOISE_LOUD = 80  # dB

    def calculate_comfort_metrics(
        self,
        temperature: float,
        humidity: float,
        co2_level: float,
        noise_level: float
    ) -> Dict:
        """
        Calculate comprehensive comfort metrics from sensor data

        Args:
            temperature: Room temperature in Celsius
            humidity: Relative humidity in percentage
            co2_level: CO2 level in ppm
            noise_level: Noise level in dB

        Returns:
            Dictionary containing comfort scores and status indicators
        """

        # Calculate individual comfort scores (0-100)
        thermal_score = self._calculate_thermal_comfort(temperature, humidity)
        air_quality_score = self._calculate_air_quality(co2_level)
        noise_score = self._calculate_noise_comfort(noise_level)

        # Overall comfort score (weighted average)
        overall_score = (thermal_score * 0.35 + air_quality_score * 0.35 + noise_score * 0.30)

        return {
            "comfort_score": round(overall_score, 1),
            "comfort_level": self._get_comfort_level(overall_score),
            "thermal_comfort": self._get_thermal_comfort_status(temperature, humidity),
            "thermal_score": round(thermal_score, 1),
            "air_quality": self._get_air_quality_status(co2_level),
            "air_quality_score": round(air_quality_score, 1),
            "noise_comfort": self._get_noise_status(noise_level),
            "noise_score": round(noise_score, 1),
            "breakdown": {
                "temperature": round(temperature, 1),
                "humidity": round(humidity, 1),
                "co2_ppm": round(co2_level, 0),
                "noise_db": round(noise_level, 1)
            }
        }

    def _calculate_thermal_comfort(self, temperature: float, humidity: float) -> float:
        """
        Calculate thermal comfort score based on temperature and humidity
        Uses simplified PMV-PPD model principles
        """
        # Optimal range scoring
        if self.TEMP_OPTIMAL_MIN <= temperature <= self.TEMP_OPTIMAL_MAX:
            temp_score = 100
        elif 18 <= temperature < self.TEMP_OPTIMAL_MIN or self.TEMP_OPTIMAL_MAX < temperature <= 26:
            # Acceptable range
            temp_score = 80
        else:
            # Outside acceptable range
            temp_score = max(0, 60 - abs(temperature - 22) * 5)

        # Humidity scoring
        if self.HUMIDITY_OPTIMAL_MIN <= humidity <= self.HUMIDITY_OPTIMAL_MAX:
            humidity_score = 100
        elif 30 <= humidity < self.HUMIDITY_OPTIMAL_MIN or self.HUMIDITY_OPTIMAL_MAX < humidity <= 70:
            humidity_score = 80
        else:
            humidity_score = max(0, 60 - abs(humidity - 50) * 2)

        # Combined thermal comfort (average of temp and humidity)
        return (temp_score + humidity_score) / 2

    def _calculate_air_quality(self, co2_level: float) -> float:
        """
        Calculate air quality score based on CO2 levels
        References: WHO, ASHRAE standards
        """
        if co2_level <= self.CO2_SAFE:
            return 100
        elif co2_level <= self.CO2_WARNING:
            # Linear decline from 100 to 60
            return 100 - ((co2_level - self.CO2_SAFE) / (self.CO2_WARNING - self.CO2_SAFE)) * 40
        elif co2_level <= 2000:
            # Further decline
            return 60 - ((co2_level - self.CO2_WARNING) / (2000 - self.CO2_WARNING)) * 40
        else:
            return max(10, 20 - (co2_level - 2000) / 1000)

    def _calculate_noise_comfort(self, noise_level: float) -> float:
        """
        Calculate noise comfort score
        References: ISO 3382, acoustic comfort standards
        """
        if noise_level <= 50:
            return 100
        elif noise_level <= 65:
            # Linear decline from 100 to 60
            return 100 - ((noise_level - 50) / (65 - 50)) * 40
        elif noise_level <= 80:
            # Further decline
            return 60 - ((noise_level - 65) / (80 - 65)) * 40
        else:
            return max(10, 20 - (noise_level - 80) / 5)

    def _get_comfort_level(self, score: float) -> str:
        """Convert comfort score to readable level"""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Acceptable"
        elif score >= 20:
            return "Poor"
        else:
            return "Inadequate"

    def _get_thermal_comfort_status(self, temperature: float, humidity: float) -> str:
        """Get thermal comfort status"""
        if self.TEMP_OPTIMAL_MIN <= temperature <= self.TEMP_OPTIMAL_MAX and \
           self.HUMIDITY_OPTIMAL_MIN <= humidity <= self.HUMIDITY_OPTIMAL_MAX:
            return "Optimal"
        elif 18 <= temperature <= 26 and 30 <= humidity <= 70:
            return "Comfortable"
        elif temperature > self.TEMP_OPTIMAL_MAX:
            return "Too Warm"
        elif temperature < self.TEMP_OPTIMAL_MIN:
            return "Too Cold"
        else:
            return "Check Humidity"

    def _get_air_quality_status(self, co2_level: float) -> str:
        """
        Get air quality status based on CO2 levels
        Color coding: Green (safe), Yellow (warning), Red (danger)
        """
        if co2_level <= self.CO2_SAFE:
            return "Good"  # Green
        elif co2_level <= self.CO2_WARNING:
            return "Fair"  # Yellow
        elif co2_level <= 2000:
            return "Poor"  # Orange
        else:
            return "Critical"  # Red

    def _get_noise_status(self, noise_level: float) -> str:
        """Get noise comfort status"""
        if noise_level <= self.NOISE_QUIET:
            return "Quiet"
        elif noise_level <= self.NOISE_MODERATE:
            return "Moderate"
        elif noise_level <= self.NOISE_LOUD:
            return "Loud"
        else:
            return "Very Loud"

    def predict_occupancy_impact(self, people_count: int) -> Dict:
        """
        Predict how occupancy might affect environmental metrics
        (Used for advisory generation)
        """
        return {
            "expected_co2_increase": people_count * 0.5,  # ppm per person
            "expected_noise_increase": people_count * 2,  # dB
            "expected_temperature_increase": people_count * 0.1,  # °C per person
            "crowding_level": self._classify_crowding(people_count)
        }

    def _classify_crowding(self, people_count: int) -> str:
        """Classify crowding level"""
        if people_count == 0:
            return "Empty"
        elif people_count <= 3:
            return "Quiet"
        elif people_count <= 7:
            return "Moderate"
        elif people_count <= 12:
            return "Busy"
        else:
            return "Very Busy"


# Singleton instance
_fusion_instance = None


def get_sensor_fusion():
    """Get singleton instance of SensorFusion"""
    global _fusion_instance
    if _fusion_instance is None:
        _fusion_instance = SensorFusion()
    return _fusion_instance
