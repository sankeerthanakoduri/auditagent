FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV STREAMLIT_SERVER_PORT=7860
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

ENV HOME=/home/user
ENV PATH=/home/user/.local/bin:$PATH

WORKDIR /app


# ------------------------------------------------------------
# System dependencies
# ------------------------------------------------------------

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*


# ------------------------------------------------------------
# Python dependencies
# ------------------------------------------------------------

COPY requirements.txt .

RUN pip install \
    --no-cache-dir \
    --upgrade pip

RUN pip install \
    --no-cache-dir \
    -r requirements.txt


# ------------------------------------------------------------
# Application
# ------------------------------------------------------------

COPY . .


# ------------------------------------------------------------
# Runtime user
# ------------------------------------------------------------

RUN useradd \
    -m \
    -u 1000 \
    user

RUN chown -R user:user /app

USER user


# ------------------------------------------------------------
# Runtime directories
# ------------------------------------------------------------

RUN mkdir -p \
    /app/audit_log \
    /app/data


# ------------------------------------------------------------
# Hugging Face port
# ------------------------------------------------------------

EXPOSE 7860


# ------------------------------------------------------------
# Start application
# ------------------------------------------------------------

CMD [
    "streamlit",
    "run",
    "app.py",
    "--server.address=0.0.0.0",
    "--server.port=7860"
]