# Use a Python base image
FROM python:3.12.5-slim

# Install ping command
RUN apt-get update && apt-get install -y iputils-ping

# Set working directory
WORKDIR /app

# Copy all files to the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the script
CMD ["python", "network_monitor.py"]



