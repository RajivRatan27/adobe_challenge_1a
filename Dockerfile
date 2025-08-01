# Dockerfile

# Use a slim, official Python image.
# Using python:3.10-slim-bookworm for a specific stable Debian release.
FROM python:3.10-slim-bookworm

# Set metadata labels
LABEL maintainer="adobe_challenge_1a Team"
LABEL version="1.0"
LABEL description="Intelligent PDF Outline Extractor"

# Set the working directory in the container
WORKDIR /app

# Copy requirements and wheels first
COPY requirements.txt .
COPY wheels/ ./wheels/

# Install system dependencies, then install Python packages from local wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --find-links=./wheels -r requirements.txt

# Copy the entire project context into the workdir
COPY . .

# Create directories for input and output volumes
# This is good practice even though volumes will overwrite them.
RUN mkdir -p /app/input /app/output

# Specify the command to run on container startup
CMD ["python", "round1a_implementation.py"]