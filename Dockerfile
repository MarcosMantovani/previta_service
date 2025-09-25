# Multi-stage build for better performance and smaller image size
FROM python:3.10.18-slim-bullseye as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    autoconf \
    automake \
    libtool \
    python3-dev \
    pkg-config \
    gcc \
    build-essential \
    git-core \
    binutils \
    libmagic-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libproj-dev \
    libvips-dev \
    libgraphviz-dev \
    tesseract-ocr \
    tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies first (better caching)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.10.18-slim-bullseye as production

ARG GIT_VERSION=UNDEFINED
ENV GIT_VERSION=$GIT_VERSION

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"

# Set application environment variables from ARGs
ENV SERVICE_BASE_URL=${SERVICE_BASE_URL}
ENV SERVICE_FQDN_PREVITA_SCHEDULER=${SERVICE_FQDN_PREVITA_SCHEDULER}
ENV SERVICE_FQDN_PREVITA_SERVICE=${SERVICE_FQDN_PREVITA_SERVICE}
ENV SERVICE_URL_PREVITA_SCHEDULER=${SERVICE_URL_PREVITA_SCHEDULER}
ENV SERVICE_URL_PREVITA_SERVICE=${SERVICE_URL_PREVITA_SERVICE}
ENV CANONICAL_URL=${CANONICAL_URL}
ENV DATABASE_HOST=${DATABASE_HOST}
ENV DATABASE_NAME=${DATABASE_NAME}
ENV DATABASE_PASSWORD=${DATABASE_PASSWORD}
ENV DATABASE_PORT=${DATABASE_PORT}
ENV DATABASE_URL=${DATABASE_URL}
ENV DATABASE_USER=${DATABASE_USER}
ENV DJANGO_DEBUG=${DJANGO_DEBUG}
ENV DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
ENV REDIS_DB=${REDIS_DB}
ENV REDIS_HOST=${REDIS_HOST}
ENV REDIS_PASSWORD=${REDIS_PASSWORD}
ENV REDIS_PORT=${REDIS_PORT}
ENV REDIS_URL=${REDIS_URL}
ENV REDIS_USER=${REDIS_USER}
ENV TZ=${TZ}

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    procps \
    libmagic1 \
    libcurl4 \
    libssl1.1 \
    libproj19 \
    gdal-bin \
    gettext \
    libvips42 \
    graphviz \
    tesseract-ocr \
    tesseract-ocr-por \    
    locales \
    && sed -i -e 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && locale-gen pt_BR.UTF-8 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create app directory and user
RUN groupadd -r previta && useradd -r -g previta previta
RUN mkdir -p /previta && chown previta:previta /previta

WORKDIR /previta

# Copy application code (do this last for better caching)
COPY --chown=previta:previta . /previta/
RUN rm -rf /previta/static

# Make scripts executable (now they will be copied thanks to .dockerignore fix)
RUN chmod +x /previta/start-service.sh /previta/start-service-dev.sh /previta/start-scheduler.sh /previta/start-scheduler-dev.sh /previta/wait-for-it.sh

# Switch to non-root user for security
USER previta
