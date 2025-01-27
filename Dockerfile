# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port (Cloud Run will override this with $PORT)
ENV PORT 8080
EXPOSE 8080

# Set production environment
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Set Python to run in unbuffered mode
ENV PYTHONUNBUFFERED True

# Increase timeout for gunicorn
ENV GUNICORN_TIMEOUT 120

# Run the application with increased timeout
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout ${GUNICORN_TIMEOUT} --access-logfile - --error-logfile - --log-level info app:app 