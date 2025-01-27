from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Gemini API configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Model configuration
DEFAULT_MODEL = "gemini-pro"
TEMPERATURE = 0.7
TOP_P = 0.95
TOP_K = 40
MAX_OUTPUT_TOKENS = 2048

# Agent configuration
VERBOSE = True 