FROM python:3.13-slim

WORKDIR /app

# Copy dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

# Run the bot
CMD ["python", "src/index.py"]
