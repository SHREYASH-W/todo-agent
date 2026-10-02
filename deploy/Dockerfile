FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY static/ ./static/
COPY templates/ ./templates/
COPY config/ ./config/

# Create runtime directories
RUN mkdir -p logs backups

# Initialize database
RUN python -m src.db.init_db

EXPOSE 5000

CMD ["python", "-m", "src.app"]
