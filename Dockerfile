# Use a base Python image based on a newer Debian release (Bullseye or Bookworm)
FROM python:3.10-slim-bullseye
# Alternatively, for the very latest:
# FROM python:3.10-slim-bookworm

# Set the working directory
WORKDIR /app

# Install system dependencies required for building many Python packages
# build-essential: provides gcc, g++, make, etc.
# libpq-dev: common for database connectors (if you use PostgreSQL)
# python3-dev: provides Python header files needed for C extensions
# poppler-utils: often needed for PDF processing (e.g., PyPDFLoader's underlying dependencies)
# libgl1-mesa-glx: common for libraries with graphical components or certain data science libs
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    python3-dev \
    poppler-utils \
    libgl1-mesa-glx \
    # Add other specific libraries if your logs indicate them (e.g., libjpeg-dev, zlib1g-dev)
    && rm -rf /var/lib/apt/lists/* # Clean up apt cache to reduce image size

# Upgrade pip and setuptools to ensure compatibility with newer packages
RUN pip install --upgrade pip setuptools

# Copy your requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port your app listens on
EXPOSE 8000

# Command to run your application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

