FROM mongo:latest

# Install the necessary tools for MongoDB
RUN apt-get update && apt-get install -y gnupg wget \
    && wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add - \
    && echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" > /etc/apt/sources.list.d/mongodb-org-6.0.list \
    && apt-get update \
    && apt-get install -y mongodb-org-tools \
    && rm -rf /var/lib/apt/lists/*
