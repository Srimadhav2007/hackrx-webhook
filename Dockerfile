# Use a base Python image based on a newer Debian release (Bullseye or Bookworm)
FROM python:3.10-slim-bullseye

# Set the working directory
WORKDIR /app

# --- Install system dependencies required for building Python packages and sqlite3 ---
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    python3-dev \
    poppler-utils \
    libgl1-mesa-glx \
    wget \
    # Clean up apt cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

# --- Upgrade sqlite3 from source ---
# ChromaDB requires sqlite3 >= 3.35.0. We'll install a newer version.
ENV SQLITE_VERSION 3.45.3
RUN set -ex \
    # Corrected URL for sqlite-autoconf-3.45.3.tar.gz as of recent check
    && wget https://www.sqlite.org/2024/sqlite-autoconf-3450300.tar.gz -O sqlite-autoconf-$SQLITE_VERSION.tar.gz \
    && tar xzf sqlite-autoconf-$SQLITE_VERSION.tar.gz \
    && cd sqlite-autoconf-$SQLITE_VERSION \
    && ./configure --prefix=/usr/local \
    && make \
    && make install \
    && ldconfig \
    && cd /app \
    && rm -rf sqlite-autoconf-$SQLITE_VERSION sqlite-autoconf-$SQLITE_VERSION.tar.gz

# Ensure Python's sqlite3 module uses the newly installed library
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
ENV PATH=/usr/local/bin:$PATH

# Upgrade pip and setuptools to ensure compatibility with newer packages
RUN pip install --upgrade pip setuptools

# Copy your requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port your app listens on. This is a declaration, not a binding.
EXPOSE 8000

# Command to run your application.
# Explicitly set the port to 8000, aligning with Railway's public networking setting.
# Use the exec form (with square brackets) for clarity and signal handling.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
