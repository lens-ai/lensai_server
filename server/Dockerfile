# Use Ubuntu as the base image
FROM ubuntu:20.04

# Install necessary dependencies
RUN apt-get update && apt-get install -y python3-pip

RUN apt-get install -y supervisor
# Set the working directory
WORKDIR /app

# Copy everything to /app in the container
COPY . /app

COPY supervisord.conf /etc/supervisor/supervisord.conf

COPY ../config.ini /app/config.ini

# Install dependencies
RUN pip install -r  requirements.txt

# Expose port 8000
EXPOSE 8000

# Run the server
# CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
