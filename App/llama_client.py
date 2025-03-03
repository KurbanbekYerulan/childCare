"""
Client for interacting with Google Gemini API with rate limiting.
"""

import json
import requests
import os
import time
import config
from datetime import datetime, timedelta

class LlamaClient:
    def __init__(self, api_url=None):
        """Initialize the Google Gemini client with rate limiting."""
        self.api_url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent"
        self.api_key = os.environ.get("GOOGLE_API_KEY", "MY_API")
        self.temperature = config.LLAMA_TEMPERATURE
        self.max_tokens = config.LLAMA_MAX_TOKENS
        
        # Rate limiting
        self.max_requests_per_minute = 30  # Set to half of the actual limit (60)
        self.request_timestamps = []
        self.total_requests_today = 0
        self.daily_limit = 500  # Conservative daily limit
        self.last_day_reset = datetime.now().date()
        
    def _check_rate_limit(self):
        """Check if we're within rate limits."""
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        self.request_timestamps = [ts for ts in self.request_timestamps 
                                  if current_time - ts < 60]
        
        # Check if we've hit the per-minute limit
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            wait_time = 60 - (current_time - self.request_timestamps[0])
            if wait_time > 0:
                print(f"Rate limit approached. Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
        
        # Reset daily counter if it's a new day
        today = datetime.now().date()
        if today > self.last_day_reset:
            self.total_requests_today = 0
            self.last_day_reset = today
            
        # Check daily limit
        if self.total_requests_today >= self.daily_limit:
            raise Exception(f"Daily limit of {self.daily_limit} requests reached. Please try again tomorrow.")
            
        # Add current timestamp to the list
        self.request_timestamps.append(current_time)
        self.total_requests_today += 1
        
        # Print usage stats
        print(f"Request {self.total_requests_today}/{self.daily_limit} today. " +
              f"{len(self.request_timestamps)}/{self.max_requests_per_minute} in last minute.")
        
    def test_connection(self):
        """Test the connection to the Google Gemini API."""
        if not self.api_key:
            print("Google API key not set. Please set the GOOGLE_API_KEY environment variable.")
            print("Get a free API key at: https://makersuite.google.com/app/apikey")
            return False
            
        try:
            print("Testing Google Gemini API connection...")
            
            url = f"{self.api_url}?key={self.api_key}"
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": "Hello, are you working?"}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 10
                }
            }
            
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(
                url, 
                headers=headers, 
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                print("Successfully connected to Google Gemini API")
                return True
            else:
                print(f"API returned status code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"Google Gemini API connection failed: {e}")
            return False
            
    def query(self, ocr_text, user_query):
        """
        Send OCR text and user query to Google Gemini and get a response.
        """
        try:
            if not self.api_key:
                return "Error: Google API key not set. Please set the GOOGLE_API_KEY environment variable."
                
            # Check rate limits
            self._check_rate_limit()
            
            system_prompt = config.SYSTEM_PROMPT
            prompt = f"{system_prompt}\n\nHere is the text captured from my screen:\n\n{ocr_text}\n\nBased on this content, {user_query}"
            
            url = f"{self.api_url}?key={self.api_key}"
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": self.temperature,
                    "maxOutputTokens": self.max_tokens
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }
            
            headers = {"Content-Type": "application/json"}
            
            print("Sending query to Google Gemini...")
            
            response = requests.post(
                url, 
                headers=headers, 
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    return result["candidates"][0]["content"]["parts"][0]["text"]
                else:
                    return "No response generated. This might be due to safety filters or content policy."
            elif response.status_code == 429:
                return "Rate limit exceeded. Please try again later."
            else:
                error_msg = f"Google Gemini API error: {response.status_code}"
                if "error" in response.json():
                    error_msg += f" - {response.json()['error']['message']}"
                return error_msg
                
        except Exception as e:
            return f"Error querying Google Gemini: {e}" 