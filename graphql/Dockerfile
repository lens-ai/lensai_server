# Use Ubuntu as the base image
FROM ubuntu:20.04

# Install necessary dependencies
RUN apt-get update && apt-get install -y python3-pip

# Set the working directory
WORKDIR /app

COPY ../config.ini /app/config.ini

# Install your dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY config.py database.py lensai_db.tar.gz main.py models.py resolvers.py schema.py /app/

CMD ["python3", "/app/main.py"] 
