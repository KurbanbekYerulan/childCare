"""
Configuration settings for the Screenpipe-Gemini Integration.
"""

import os
from pathlib import Path

# Screenpipe configuration
SCREENPIPE_DB_PATH = os.environ.get(
    "SCREENPIPE_DB_PATH", 
    str(Path.home() / ".screenpipe" / "screenpipe.db")
)

# Google Gemini configuration
GEMINI_API_URL = os.environ.get(
    "GEMINI_API_URL", 
    "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent"
)
LLAMA_TEMPERATURE = float(os.environ.get("GEMINI_TEMPERATURE", "0.7"))
LLAMA_MAX_TOKENS = int(os.environ.get("GEMINI_MAX_TOKENS", "1024"))  # Reduced to be conservative

# Query configuration
DEFAULT_TIME_WINDOW = int(os.environ.get("DEFAULT_TIME_WINDOW", "300"))  # 5 minutes
MAX_OCR_TEXT_LENGTH = int(os.environ.get("MAX_OCR_TEXT_LENGTH", "4000"))  # Reduced to be conservative

# System prompt for Gemini
SYSTEM_PROMPT = """You are an assistant that helps analyze screen content captured by Screenpipe.
Your task is to answer questions about what the user has seen on their screen.
The text provided comes from OCR (Optical Character Recognition) of screen captures,
so it may contain errors or incomplete information.
Be concise and focus on extracting the most relevant information from the screen content.
""" 