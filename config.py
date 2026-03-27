import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# future use
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# provider switch (IMPORTANT)
SMS_PROVIDER = os.getenv("SMS_PROVIDER", "mock")
