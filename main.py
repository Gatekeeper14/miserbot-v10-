# Use official Python image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Copy requirements and install in a virtual environment
COPY requirements.txt .

# Create a virtual environment
RUN python -m venv .venv

# Upgrade pip inside venv
RUN .venv/bin/pip install --upgrade pip

# Install dependencies inside venv
RUN .venv/bin/pip install -r requirements.txt

# Copy your bot code
COPY . .

# Expose Flask port
EXPOSE 5000

# Set environment variable for Flask
ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run the bot
CMD ["/app/.venv/bin/python", "main.py"]
