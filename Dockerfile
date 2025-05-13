# Use Python 3.10 slim image as base
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy only requirements file first to leverage Docker cache
COPY pyproject.toml setup.py /app/

# Install all dependencies using uv
RUN uv pip install -e .

# Copy the actual application code
COPY . /app/

# Expose the port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["tripit-mcp"]
