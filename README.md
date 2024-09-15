# Lens AI Server - Data and Model Monitoring Library for Edge AI Applications
Lens AI Server is a comprehensive solution for collecting, aggregating, and monitoring sensor data and metrics for Edge AI applications. It provides an easy-to-use platform to observe and analyze key metrics through dashboards, enabling efficient monitoring and performance optimization of your AI models.

## The following Lens AI tools
- Lens AI Python Profiler : https://github.com/lens-ai/lensai_profiler_python
- Lens AI C++ Profiler : https://github.com/lens-ai/lensai_profiler_cpp
- Lens AI Monitoring Server : (The current repo)

![Alt text](https://github.com/lens-ai/lensai_server/blob/main/server.png)

### Lens AI monitoring server Components
The Lens AI Server comprises five major components:
1. Lens AI Sensor Data Handler: Manages sensor HTTP requests and stores incoming sensor data.
2. Lens AI Workers: Aggregates, transforms, and extracts metric data from sensor inputs for analysis.
3. Lens AI GraphQL Server: Provides a GraphQL endpoint to fetch the aggregated metrics, enabling flexible and efficient data retrieval.
4. Lens AI Monitoring Server: Uses Grafana to build interactive dashboards for monitoring key metrics.
5. Lens AI Database: Utilizes MongoDB to store sensor data and metrics for persistent and scalable storage.

## Usage
```sh
git clone the lensai_server repo
```
### Server Configuration
```sh
nano config.ini 
```
### Build the docker containers
```sh
docker-compose up --build -d 
```
### Lens AI server Configuration

Adjust the config file based on the proejct requirements mainly . Please don't change the DB collection names.

- [DEFAULT]
- PROJECT_ID = your project id
- SLEEP_INTERVAL = 10 (Sleep interv of the workers)
- NUM_WORKERS = 1 (Number of worker threads)

- [paths]
- BASE_PATH = /tmp (Base path is the path under which the data is mounted on the container)

### Lens AI sensor data handler :
The sensor data handler runs on port 8000 and can be accessed at http://localhost:8000 on the host machine. To change the host port, modify the docker-compose.yml file to your preferred port.

### Lens AI Dashboard:
The Lens AI Dashboard is accessible on port 3000 on the host machine. Access it via http://localhost:3000.

### Screenshots of the Dashboard
![Alt text](https://github.com/lens-ai/lensai_server/blob/main/Dashboard_1.png)

![Alt text](https://github.com/lens-ai/lensai_server/blob/main/Dashboard_2.png)

![Alt text](https://github.com/lens-ai/lensai_server/blob/main/Dashboard_3.png)

#### Important Notes:
In the Lens AI Dashboard for the panels make sure 
1. GraphQL URL Configuration: Ensure the GraphQL URL in the Grafana panels is configured correctly as shown in the image below.
![Alt text](https://github.com/lens-ai/lensai_server/blob/main/Dashboard_URL.png)

2. GraphQL Query: Verify that the GraphQL query contains the correct parameters and query values.
![Alt text](https://github.com/lens-ai/lensai_server/blob/main/Dashboard_Query.png)



Software Stack
Lens AI Server is built using the following technologies:

- FastAPI: Provides a high-performance web framework for the sensor data handler.
- Strawberry: A GraphQL library for Python that powers the GraphQL server.
- Datasketches: Used for efficient and scalable data sketches for metrics calculations.
- Grafana: Offers powerful and flexible dashboards for real-time monitoring.
- MongoDB: A NoSQL database for storing and managing sensor data and metrics.
