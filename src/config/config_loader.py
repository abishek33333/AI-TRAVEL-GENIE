import os
from dotenv import load_dotenv

# Load .env file for local development
# In HF Spaces, this file won't exist, and the app will skip this line
load_dotenv() 

class Config:
    """Centralized configuration for the application."""
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME", "llama3-70b-8192") # Includes a default fallback

# Create an instance for other files to use
config = Config()