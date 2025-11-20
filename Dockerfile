# EMPIRE v13 - Multi-stage Production Dockerfile
# Stage 1: Base with system dependencies
FROM python:3.12-slim AS base

# Install Node.js 20 and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    xdg-utils \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Stage 2: Dependencies
FROM base AS dependencies

# Copy dependency files
COPY package.json package-lock.json* ./
COPY pyproject.toml ./

# Install Node.js dependencies
RUN npm ci --production --ignore-scripts

# Install Python dependencies from pyproject.toml
RUN pip install --no-cache-dir .

# Install Chromium for Playwright
RUN playwright install chromium --with-deps

# Stage 3: Production
FROM base AS production

# Copy installed dependencies from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin
COPY --from=dependencies /app/node_modules /app/node_modules
COPY --from=dependencies /root/.cache/ms-playwright /root/.cache/ms-playwright

# Copy application code
COPY . /app

# Create necessary directories
RUN mkdir -p /app/sessions/whatsapp /app/sessions/facebook /app/data

# Set working directory
WORKDIR /app

# Expose port for Baileys HTTP server (internal only)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import os; assert os.path.exists('/app/data/empire.db') or True"

# Start the bot
CMD ["python", "main.py"]
