FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Use cached layer for dependencies
COPY . /app
EXPOSE 5000

# Run the Flask app
CMD ["python", "app.py"]
