# Monitoring-Tools/Dockerfile
# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install "fastapi[standard]"

# Copy the rest of the application code
COPY . .

# Set entrypoint script for running migration, import_sites, and FastAPI server
CMD ["sh", "-c", "python metman.py migrate && python metman.py import_sites --csv=desert_media.csv && uvicorn api:app --host 0.0.0.0 --port 8080"]
