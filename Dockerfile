FROM python:3.11

WORKDIR /app

# Set PYTHONPATH to ensure 'app' module is found
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Port EXPOSE removed (Render will use $PORT)

CMD ["python3", "-m", "app.main"]
