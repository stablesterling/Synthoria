# Use official Python slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install ffmpeg and curl
RUN apt-get update && apt-get install -y ffmpeg curl && rm -rf /var/lib/apt/lists/*

# Copy all app files
COPY . .

# Expose the port for Render
EXPOSE 10000

# Start app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
