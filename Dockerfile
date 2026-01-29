# =========================
# Hugging Face Docker Space
# =========================

# FROM python:3.11-slim

# # Set working directory
# WORKDIR /app

# # Environment settings
# ENV PYTHONUNBUFFERED=1 \
#     PYTHONDONTWRITEBYTECODE=1 \
#     PIP_NO_CACHE_DIR=1 \
#     PIP_DISABLE_PIP_VERSION_CHECK=1

# # Install system dependencies
# RUN apt-get update && apt-get install -y \
#     gcc \
#     g++ \
#     curl \
#     pkg-config \
#     libcairo2-dev \
#     libpango1.0-dev \
#     libjpeg-dev \
#     libgif-dev \
#     cmake \
#     && rm -rf /var/lib/apt/lists/*


# # Copy dependency file
# COPY requirements.txt .

# # Install Python dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy full project
# COPY . .

# # Hugging Face requires port 7860
# EXPOSE 7860

# # Run Streamlit app
# # CMD ["streamlit", "run", "streamlit_app.py", "--server.port=7860", "--server.address=0.0.0.0"]
# CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
FROM python:3.11-slim

WORKDIR /app

# 1. Environment variables to prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# 2. System dependencies (Correct for ReportLab/Cairo)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    pkg-config \
    libcairo2-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 3. Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# 4. Copy App code
COPY . .

# 5. Expose the port (Hugging Face Spaces defaults to 7860)
EXPOSE 7860

# 6. Start ONLY Streamlit
# Since app.py imports the logic from main.py, we don't need uvicorn running!
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]