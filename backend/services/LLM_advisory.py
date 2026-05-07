#!/usr/bin/env python3
"""
LLM Advisory Service
Generates natural language advisory messages based on sensor data
Uses Claude or GPT to create helpful, context-aware recommendations
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


class AdvisoryService:
    """
    Generates natural language advisory messages for the dashboard
    """

    def __init__(self):
        self.use_llm = os.getenv('USE_LLM', 'false').lower() == 'true'
        self.llm_provider = os.getenv('LLM_PROVIDER', 'anthropic')  # 'anthropic' or 'openai'

        if self.use_llm:
            if self.llm_provider == 'anthropic':
                try:
                    from anthropic import Anthropic
                    self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
                except ImportError:
                    logger.warning("Anthropic library not installed. Falling back to rule-based advisory.")
                    self.use_llm = False
            elif self.llm_provider == 'openai':
                try:
                    from openai import OpenAI
                    self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                except ImportError:
                    logger.warning("OpenAI library not installed. Falling back to rule-based advisory.")
                    self.use_llm = False

    def generate_advisory(
        self,
        people_count: int,
        co2_level: float,
        temperature: float,
        humidity: float,
        noise_level: float,
        comfort_score: float,
        location: Optional[str] = "IT Helpdesk"
    ) -> str:
        """
        Generate an advisory message based on current sensor readings

        Args:
            people_count: Number of people detected
            co2_level: CO2 level in ppm
            temperature: Room temperature in Celsius
            humidity: Relative humidity in percentage
            noise_level: Noise level in dB
            comfort_score: Overall comfort score (0-100)
            location: Location name for context

        Returns:
            Natural language advisory message
        """

        if self.use_llm:
            return self._generate_llm_advisory(
                people_count, co2_level, temperature, humidity, noise_level, comfort_score, location
            )
        else:
            return self._generate_rule_based_advisory(
                people_count, co2_level, temperature, humidity, noise_level, comfort_score, location
            )

    def _generate_llm_advisory(
        self,
        people_count: int,
        co2_level: float,
        temperature: float,
        humidity: float,
        noise_level: float,
        comfort_score: float,
        location: str
    ) -> str:
        """Generate advisory using LLM"""
        try:
            prompt = self._create_advisory_prompt(
                people_count, co2_level, temperature, humidity, noise_level, comfort_score, location
            )

            if self.llm_provider == 'anthropic':
                message = self.client.messages.create(
                    model="claude-3-haiku-20240307",  # Using efficient model for real-time
                    max_tokens=150,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                return message.content[0].text.strip()

            elif self.llm_provider == 'openai':
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo",
                    max_tokens=150,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating LLM advisory: {e}")
            # Fall back to rule-based
            return self._generate_rule_based_advisory(
                people_count, co2_level, temperature, humidity, noise_level, comfort_score, location
            )

    def _generate_rule_based_advisory(
        self,
        people_count: int,
        co2_level: float,
        temperature: float,
        humidity: float,
        noise_level: float,
        comfort_score: float,
        location: str
    ) -> str:
        """Generate advisory using rule-based logic"""

        # Determine occupancy status
        if people_count == 0:
            occupancy_message = f"✓ {location} is currently EMPTY."
        elif people_count <= 3:
            occupancy_message = f"✓ {location} is very quiet with {people_count} person{'s' if people_count != 1 else ''}."
        elif people_count <= 7:
            occupancy_message = f"⚠ {location} is moderately busy with {people_count} people."
        elif people_count <= 12:
            occupancy_message = f"⚠⚠ {location} is BUSY with {people_count} people."
        else:
            occupancy_message = f"✗ {location} is very crowded with {people_count}+ people."

        # Determine time recommendation
        if people_count <= 3:
            time_recommendation = "Good time to visit!"
        elif people_count <= 7:
            time_recommendation = "Consider waiting a bit for fewer crowds."
        else:
            time_recommendation = "Better to come back later."

        # Determine comfort-related notes
        comfort_notes = []

        if co2_level > 1500:
            comfort_notes.append("⚠ Air quality could be better - consider ventilation.")
        if noise_level > 70:
            comfort_notes.append("⚠ It's quite noisy right now.")
        if temperature > 24:
            comfort_notes.append("⚠ Room is a bit warm.")
        elif temperature < 20:
            comfort_notes.append("⚠ Room is a bit cool.")

        # Build final message
        message_parts = [occupancy_message, time_recommendation]
        if comfort_notes:
            message_parts.extend(comfort_notes)

        return " ".join(message_parts)

    def _create_advisory_prompt(
        self,
        people_count: int,
        co2_level: float,
        temperature: float,
        humidity: float,
        noise_level: float,
        comfort_score: float,
        location: str
    ) -> str:
        """Create prompt for LLM"""

        return f"""You are a helpful assistant for a university service queue prediction system.
Given the current conditions at the {location}, provide a brief 1-2 sentence advisory message 
that helps students and staff decide whether now is a good time to visit.

Current Conditions:
- People in queue: {people_count}
- CO2 level: {co2_level:.0f} ppm
- Temperature: {temperature:.1f}°C
- Humidity: {humidity:.1f}%
- Noise level: {noise_level:.1f} dB
- Overall Comfort Score: {comfort_score:.0f}/100

Requirements:
1. Be friendly and encouraging
2. If crowded, suggest coming back later
3. If it's quiet, recommend visiting now
4. Only mention comfort issues if they're severe
5. Keep it to one or two sentences maximum
6. Use simple language

Advisory message:"""

    def generate_simple_advisory(self, people_count: int, location: str = "IT Helpdesk") -> str:
        """
        Generate a simple, quick advisory message based only on queue length
        Useful when not all sensor data is available
        """
        if people_count == 0:
            return f"✓ {location} is currently empty. Great time to visit!"
        elif people_count <= 2:
            return f"✓ {location} has very few people. Good time to visit!"
        elif people_count <= 5:
            return f"⚠ {location} is a bit busy. You might wait a few minutes."
        elif people_count <= 10:
            return f"⚠⚠ {location} is quite busy. Consider coming back later."
        else:
            return f"✗ {location} is very crowded. Better to visit another time."

    def get_advisory_with_metadata(
        self,
        people_count: int,
        co2_level: float,
        temperature: float,
        humidity: float,
        noise_level: float,
        comfort_score: float,
        location: str = "IT Helpdesk"
    ) -> dict:
        """
        Generate advisory message with additional metadata

        Returns:
            Dictionary containing message and metadata for UI
        """
        message = self.generate_advisory(
            people_count, co2_level, temperature, humidity, noise_level, comfort_score, location
        )

        # Determine recommendation level
        if people_count <= 3:
            recommendation = "VISIT_NOW"
            color = "green"
        elif people_count <= 7:
            recommendation = "MODERATE"
            color = "yellow"
        else:
            recommendation = "AVOID"
            color = "red"

        return {
            "message": message,
            "recommendation": recommendation,
            "color": color,
            "estimated_wait_minutes": people_count * 2,
            "comfort_suitable": comfort_score >= 60,
            "timestamp": None  # Will be set by caller
        }
