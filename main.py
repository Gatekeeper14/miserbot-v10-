# Use official Python slim image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Copy requirements and install in a virtual environment
COPY requirements.txt .

# Create virtual environment
RUN python -m venv .venv

# Upgrade pip and install dependencies inside venv
RUN .venv/bin/pip install --upgrade pip
RUN .venv/bin/pip install -r requirements.txt

# Copy bot code
COPY . .

# Expose Flask port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
ENV FLASK_RUN_HOST=0.0.0.0
ENV TELEGRAM_TOKEN=your_telegram_token_here

# Use Gunicorn to run the Flask app with 4 workers
CMD ["/app/.venv/bin/gunicorn", "--workers", "4", "--bind", "0.0.0.0:5000", "main:app"]
