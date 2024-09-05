# Real-Time Distributed Network Telemetry with Isolation-Based Outlier Analysis

## Objective

Real-Time Distributed Network Telemetry with Isolation-Based Outlier Analysis is a project designed for real-time network performance monitoring, anomaly detection, and visualization. The project makes use of containerized microservices orchestrated by Nomad and managed through Vagrant and VirtualBox allowing for an independent distribution. It also uses machine learning techniques, such as Isolation Forest, to detect anomalies in network behavior, making it a viable tool for ensuring network reliability and performance across distributed systems.

## Technologies and Software Used

- **Development Environment**: Visual Studio Code (VS Code)
- **Programming Language**: Python 3.
- **Libraries and Packages**:
  - `pingparsing`: For parsing ping results and extracting network metrics.
  - `ping3`: For calculating network jitter.
  - `numpy` and `scikit-learn`: For AI-based anomaly detection using the Isolation Forest model.
  - `influxdb-client`: For interacting with the InfluxDB database.
  - `statistics`: For calculating network statistics like standard deviation.
- **Databases and Visualization**:
  - **InfluxDB**: For logging and storing network telemetry data.
  - **Grafana**: For real-time data visualization and queries using InfluxDB as a data source.
- **Virtualization and Orchestration**:
  - **Vagrant**: For managing virtual machine environments.
  - **VirtualBox**: VM management to work with Vagrant.
  - **Docker**: For containerizing the Python application, InfluxDB, and Grafana.
  - **Nomad**: For orchestrating Docker containers across distributed environments.
  - **Consul**: For service discovery and configuration management within Nomad.

## Overview of the Network Monitoring Python Script (`network_monitor.py`)

The `network_monitor.py` script is the core of the monitoring system. It continuously pings specified IP addresses to measure network performance and logs the metrics to InfluxDB. Below is a brief overview of each function in the script:

1. **InfluxDB Client Configuration**: Establishes a secure connection to InfluxDB using environment variables for authentication (`INFLUXDB_TOKEN`, `INFLUXDB_ORG`, `INFLUXDB_BUCKET`).

2. **`write_to_influxdb(data, measurement)`**: This function writes the collected network metrics to InfluxDB. It handles exceptions and ensures each data point is timestamped.

3. **`ping_addresses(ip_list)`**: Pings a list of IP addresses and collects metrics such as round-trip time (RTT), packet loss, standard deviation and jitter. It uses `pingparsing` for metric extraction.

4. **`calculate_jitter(ip, count)`**: Uses `ping3` to computes the network jitter for a given IP address by sending multiple pings and calculating the standard deviation of RTT values.

5. **`detect_anomalies(data)`**: Utilizes the Isolation Forest model from `scikit-learn` to detect anomalies in the network performance data. Detected anomalies are logged separately in InfluxDB.

6. **`log_results_to_file(results, filename="network_metrics.json")`**: Logs only the ping results from the `pingparsing` to a local JSON file for offline analysis or testing purposes.

7. **`main()`**: The main function continuously monitors the specified IP addresses, logs the results, detects anomalies, and repeats the process after a defined interval.

## Setup and Usage Guide

### Prerequisites

1. **Development Environment**:
   - Install [Visual Studio Code (VS Code)](https://code.visualstudio.com/) or any IDE of your choice.
   - Install Python 3.x from the [official Python website](https://www.python.org/downloads/).

2. **Create a Python Virtual Environment**:
   - Open your IDE terminal.
   - Navigate to the project directory.
   - Create a virtual environment to avoid conflicts with global Python packages:
     ```bash
     python -m venv venv
     ```
   - Activate the virtual environment:
     - On Windows: `venv\Scripts\activate`
     - On MacOS/Linux: `source venv/bin/activate`

3. **Install Python Dependencies**:
   - Ensure you're in the virtual environment.
   - Install the required Python packages:
     ```bash
     pip install -r requirements.txt
     ```

4. **Set Up Environment Variables**:
   - Create a `.env` file in the root directory.
   - Define your InfluxDB and Grafana credentials and other sensitive information:
     ```env
     INFLUXDB_TOKEN=your_influxdb_token
     INFLUXDB_ORG=your_organization_name
     INFLUXDB_BUCKET=your_bucket_name
     GRAFANA_ADMIN_USER=grafana_username
     GRAFANA_ADMIN_PASSWORD=grafana_password
     ```

5. **Install Vagrant and VirtualBox**:
   - Download and install [Vagrant](https://www.vagrantup.com/downloads).
   - Download and install [VirtualBox](https://www.virtualbox.org/wiki/Downloads).
   - Ensure that the VirtualBox Host-only Network is configured according to the IPs used in the `Vagrantfile`.

6. **Configure and Sync Docker-Compose Folder**:
   - Ensure the folder containing `docker-compose.yml` is correctly synced with the Vagrant VM using the `synced_folder` directive in the `Vagrantfile`.

7. **Deploy Nomad Server and Client**:
   - Open a terminal and navigate to the folder containing the `Vagrantfile`.
   - Run the following command to bring up the Vagrant environment:
     ```bash
     vagrant up
     ```
   - SSH into the Nomad server:
     ```bash
     vagrant ssh nomad-server
     ```
   - Once inside, navigate to the folder with the Nomad job and then run the job:
     ```bash
     nomad job run docker-compose.nomad
     ```

8. **Access Network Monitoring Data**:
   - Once the Nomad job is completed, access InfluxDB through the IP defined for the nomad server with the port of 8086 for InfluxDB. Using your credentials, log into InfluxDB and use Data Explorer to view the logged network data.
   - Similarly, once InfluxDB is up and running, access Grafana through the port of 3000, log in and configure Grafana to connect with the InfluxDB data source:
     - Go to Grafana's settings and add a new data source.
     - Choose InfluxDB and provide the necessary credentials and URLs.
     - Use `InfluxQL` queries to make your own queries in Grafana to visualize the data.

### Additional Notes

- **Anomaly Detection**: The `detect_anomalies` function will log anomalies separately in InfluxDB. You can set up alerts in Grafana to be notified when anomalies are detected.
- **Data Visualization**: Use Grafana dashboards to visualize metrics such as latency, packet loss, and jitter. Customize your dashboards to include tables, graphs, and alerts based on your needs.

## Contact Information

For any questions or feedback, please contact me at masoodofficial27@gmail.com.
