FROM python:3.11

WORKDIR /app

# Set PYTHONPATH to ensure 'app' module is found
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port (Render will use $PORT anyway)
EXPOSE 8080

CMD ["python", "-m", "app.main"]
