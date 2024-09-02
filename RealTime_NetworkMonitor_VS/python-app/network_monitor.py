import pingparsing
import time
import json
import os
from datetime import datetime, timezone  # Import timezone
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


# InfluxDB client configuration
influxdb_url = "http://influxdb:8086"
token = os.getenv("INFLUXDB_TOKEN")  # Ensure it only uses environment variable
org = os.getenv("INFLUXDB_ORG")  # Also ensure organization and bucket are loaded from environment variables
bucket = os.getenv("INFLUXDB_BUCKET")

# Check if all required environment variables are set
if not token or not org or not bucket:
    raise ValueError("Environment variables for InfluxDB are not set properly. Please check your .env file.")


# Initiate the client and writing data with our settings
client = InfluxDBClient(url=influxdb_url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)


# A function to write the results to InfluxDB
def write_to_influxdb(data):
    try:
        # Debugging information
        print(f"Writing data to InfluxDB: {data}")

        # Check for None values and replace them with 0.0 or appropriate defaults
        packet_loss = data.get("packet_loss", 0.0)
        avg_rtt = data.get("avg_rtt", 0.0)
        max_rtt = data.get("max_rtt", 0.0)
        min_rtt = data.get("min_rtt", 0.0)
        stddev_rtt = data.get("stddev_rtt", 0.0)

        # Create a point and write to InfluxDB
        point = (
            Point("ping_metrics")
            .tag("ip", data["ip"])
            .field("packet_loss", packet_loss)
            .field("avg_rtt", avg_rtt)
            .field("max_rtt", max_rtt)
            .field("min_rtt", min_rtt)
            .field("stddev_rtt", stddev_rtt)
            .time(datetime.now(timezone.utc))  # Use timezone-aware datetime object
        )

        write_api.write(bucket=bucket, org=org, record=point)
        print(f"Data written to InfluxDB for IP: {data['ip']}")

    except Exception as e:
        print(f"Error writing to InfluxDB: {e}")

        
        
# This function takes a parameter ip_list which is a list of IP addresses and hostnames
def ping_addresses(ip_list):
    ping_parser = pingparsing.PingParsing()  # Creates an instance of PingParsing from pingparsing library.
    transmitter = pingparsing.PingTransmitter()  # Used for sending ping requests to the specified IP addresses

    results = []  # This list will store network metrics (ping results) for each IP Address in the ip_list

    for ip in ip_list:
        transmitter.destination = ip  # Transmitter configured to ping this specific IP in the ip_list
        transmitter.count = 4  # 4 ping requests will be sent to the IP address
        
        try:
            response = transmitter.ping()  # Stores the response of the ping

            # Parse the ping results
            result = ping_parser.parse(response).as_dict()  # Convert the parsed result into a python dictionary

            # Log the results
            log_data = {
                "ip": ip,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "packet_loss": result.get('packet_loss_rate', 0.0),
                "avg_rtt": result.get('rtt_avg', 0.0),  # Round trip time average
                "max_rtt": result.get('rtt_max', 0.0),
                "min_rtt": result.get('rtt_min', 0.0),
                "stddev_rtt": result.get('rtt_stddev', 0.0)
            }

            print(f"Ping result for {ip}: {log_data}")
            results.append(log_data)

            # Write the results to InfluxDB
            write_to_influxdb(log_data)

        except Exception as e:
            print(f"Error pinging {ip}: {e}")

    return results

# This function will log the results from the ping_address function into JSON format file
def log_results_to_file(results, filename="network_metrics.json"):
    try:
        # Read existing data
        try:
            with open(filename, 'r') as file:
                existing_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = []

        # Append new results to the existing data
        existing_data.extend(results)
        
        # Write updated data back to the file
        with open(filename, 'w') as file:
            json.dump(existing_data, file, indent=4)
        
        print(f"Results logged to {filename}")
    except Exception as e:
        print(f"Error while logging results to file: {e}")

def main():
    # For test purposes, I use the following list of IP addresses/hostnames to monitor
    ip_list = ["8.8.8.8", "8.8.4.4", "1.1.1.1"]  # Google and Cloudflare DNS

    # Will continuously monitor the network
    while True:
        # Ping the IP addresses and get the results
        results = ping_addresses(ip_list)

        # Log the results to a file using the func created earlier
        log_results_to_file(results)

        # Have a time interval of 60 seconds before the next ping
        time.sleep(60)

# Ensuring the function is only called when the script is running directly
if __name__ == "__main__":
    main() 
