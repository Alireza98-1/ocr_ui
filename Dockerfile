# ====================================================================
# Final, Production-Ready Dockerfile
# ====================================================================

# -------------------- Stage 1: Builder --------------------
FROM python:3.11-slim AS builder
ARG REQ_FILE=requirements/base.txt
WORKDIR /opt
RUN python -m venv venv
COPY requirements/ ./requirements/
RUN . /opt/venv/bin/activate && pip install --timeout=600 -r ${REQ_FILE}

# -------------------- Stage 2: Final Image --------------------
FROM python:3.11-slim

# 1. Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libgl1-mesa-glx \
    fonts-dejavu-core \
    ffmpeg libsm6 libxext6 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 2. Create non-root user
RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /home/appuser/

# 3. Copy application files
COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser assets/ ./assets/
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser static/ ./static/           
COPY --chown=appuser:appuser templates/ ./templates/  
COPY --chown=appuser:appuser master_config.json .

# 4. Switch to the non-root user as a default
USER appuser

# 5. Set the environment PATH
ENV PATH="/opt/venv/bin:$PATH"

# 6. Expose the port and define the default command
EXPOSE 8084
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8084"]