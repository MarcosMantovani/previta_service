# Multi-stage build for better performance and smaller image size
FROM python:3.10.18-slim-bullseye as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

ENV FFMPEG_BIN=/opt/ffmpeg/bin/ffmpeg \
    FFPROBE_BIN=/opt/ffmpeg/bin/ffprobe


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

######################################################################
# FFmpeg (versão recente, já com suporte ao filtro arnndn) + modelo RNN
######################################################################
# Copia os arquivos locais para o container
COPY resources/ffmpeg-master-latest-linux64-gpl.tar.xz /tmp/ffmpeg.tar.xz
COPY resources/sh.rnnn /usr/local/share/rnnoise-model.rnn

# 1) extrai o build estático (Linux x86-64) do arquivo local
RUN mkdir -p /opt/ffmpeg \
    && tar -xJf /tmp/ffmpeg.tar.xz -C /opt/ffmpeg --strip-components=1 \
    # 2) coloca os binários no PATH antes dos que vieram do apt
    && ln -sf /opt/ffmpeg/bin/ffmpeg  /usr/local/bin/ffmpeg  \
    && ln -sf /opt/ffmpeg/bin/ffprobe /usr/local/bin/ffprobe \
    # 3) limpeza
    && rm /tmp/ffmpeg.tar.xz

# (opcional) verificação rápida durante o build — não afeta a imagem final
RUN ffmpeg -hide_banner -filters | grep arnndn

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

# Copy ffmpeg binaries from builder stage
COPY --from=builder /opt/ffmpeg /opt/ffmpeg
COPY --from=builder /usr/local/bin/ffmpeg /usr/local/bin/ffmpeg
COPY --from=builder /usr/local/bin/ffprobe /usr/local/bin/ffprobe
COPY --from=builder /usr/local/share/rnnoise-model.rnn /usr/local/share/rnnoise-model.rnn

# Create app directory and user
RUN groupadd -r previta && useradd -r -g previta previta
RUN mkdir -p /previta && chown previta:previta /previta

WORKDIR /previta

# Copy application code (do this last for better caching)
COPY --chown=previta:previta . /previta/
RUN rm -rf /previta/static

# Switch to non-root user for security
USER previta
