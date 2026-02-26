# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install CPU-only PyTorch first so sentence-transformers doesn't pull in CUDA (~2GB).
# Required for low-memory / CPU-only environments (e.g. Render, Cloud Run).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Expose port 8000 for FastAPI
EXPOSE 8000

# Command to run the app
# Entry point is root main.py (not app.main). See MIGRATION_AND_ARCHITECTURE.md.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
