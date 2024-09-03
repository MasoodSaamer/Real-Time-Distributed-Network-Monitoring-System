import pingparsing
import time
import json
import os
#import random # For testing simulated latency delays
from datetime import datetime, timezone  # Import timezone
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from ping3 import ping # For jitter calculation
import statistics
from sklearn.ensemble import IsolationForest # For anomaly detection using isolation forest model
import numpy as np


# InfluxDB client configuration. Unless you plan to have your program be fully local, change the token, org and bucket values in the .env environment
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
def write_to_influxdb(data, measurement="ping_metrics"):
    try:
        # Debugging information
        print(f"Writing data to InfluxDB: {data}")

        # Check for None values and replace them with 0.0. InfluxDB wont register null values.
        packet_loss = data.get("packet_loss", 0.0)
        avg_rtt = data.get("avg_rtt", 0.0)
        max_rtt = data.get("max_rtt", 0.0)
        min_rtt = data.get("min_rtt", 0.0)
        stddev = data.get("stddev", 0.0)
        jitter = data.get("jitter", 0.0)

        # Create a point and write to InfluxDB
        point = (
            Point(measurement)
            .tag("ip", data["ip"])
            .field("packet_loss", packet_loss)
            .field("avg_rtt", avg_rtt)
            .field("max_rtt", max_rtt)
            .field("min_rtt", min_rtt)
            .field("stddev", stddev)
            .field("jitter", jitter)
            .time(datetime.now(timezone.utc))  # Use timezone-aware datetime object
        )

        write_api.write(bucket=bucket, org=org, record=point)
        print(f"Data written to InfluxDB for IP: {data['ip']}") # Confirmation

    except Exception as e:
        print(f"Error writing to InfluxDB: {e}") 

        
        
# This function takes a parameter ip_list which is a list of IP addresses and hostnames defined in the main()
def ping_addresses(ip_list):
    ping_parser = pingparsing.PingParsing()  # Creates an instance of PingParsing from pingparsing library.
    transmitter = pingparsing.PingTransmitter()  # Used for sending ping requests to the specified IP addresses

    results = []  # This list will store network metrics (ping results) for each IP Address in the ip_list

    for ip in ip_list:
        transmitter.destination = ip  # Transmitter configured to ping this specific IP in the ip_list
        transmitter.count = 4  # 4 ping requests will be sent to the IP address

	    # Simulate high latency by adding a delay before each ping. Uncomment if you want to test
        #simulated_latency = random.uniform(0.5, 2.0)  # Latency between 0.5 to 2 seconds
        #print(f"Simulating latency of {simulated_latency:.2f} seconds for IP: {ip}")
        #time.sleep(simulated_latency)  # Introduce the simulated latency
    
        try:
            response = transmitter.ping()  # Stores the response of the ping

            # Print raw ping output for debugging. Use this if you want to see the raw ping output
            #print(f"Raw ping output for {ip}:\n{response}")

            # Parse the ping results
            result = ping_parser.parse(response).as_dict()  # Convert the parsed result into a python dictionary

            # Collect RTTs from result to compute standard deviation (stddev)
            rtt_values = [result.get('rtt_avg', 0.0), result.get('rtt_max', 0.0), result.get('rtt_min', 0.0)]
            rtt_values = [rtt for rtt in rtt_values if rtt > 0]  # Filter out zero or non-positive RTT values
            # Calculate stddev of RTT if there are multiple RTT values
            if len(rtt_values) > 1:
                stddev = round(statistics.stdev(rtt_values), 2)  # Round to 2 dp
            else:
                stddev = 0.0  # Set stddev to 0 if insufficient RTT data

            # Calculate the jitter of our ip 
            jitter = calculate_jitter(ip)

            # Simulate packet loss. Uncomment if you want to test
            #if random.uniform(0, 1) < 0.1:  # 10% chance to simulate packet loss
            #    print(f"Simulating packet loss for IP: {ip}")
            #    result['packet_loss_rate'] = 100.0  # Set packet loss to 100%



            # Log the results
            log_data = {
                "ip": ip,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "packet_loss": result.get('packet_loss_rate', 0.0),
                "avg_rtt": result.get('rtt_avg', 0.0),  
                "max_rtt": result.get('rtt_max', 0.0),
                "min_rtt": result.get('rtt_min', 0.0),
                "stddev": stddev,
                "jitter": jitter
            }

            print(f"Ping result for {ip}: {log_data}")
            results.append(log_data)

            # Write the results to InfluxDB
            write_to_influxdb(log_data)

        except Exception as e:
            print(f"Error pinging {ip}: {e}")

    return results

# Function to calculate jitter using ping3
def calculate_jitter(ip, count=4):  # Sending 4 ICMP packet requests to the ip
    rtt_list = []

    try:
        for _ in range(count):
            rtt = ping(ip, timeout=1) # Perform the ping using ping3 and get RTT in seconds
            if rtt:
                rtt_list.append(rtt * 1000)

        # Calculate the standard deviation for RTTs which will be the jitter
        if len(rtt_list) > 1:
            jitter = round(statistics.stdev(rtt_list), 2) # Round to 2 dp
        else:
            jitter = 0.0  # in case of a single ping

    except Exception as e:
        print(f"Error calculating jitter for {ip}: {e}")
        jitter = 0.0  # Fallback value

    return jitter

# Anomaly detection function using Isolation Forest from scikit-learn
def detect_anomalies(data):
    try:
        # Convert the dictionary data within data list to a NumPy array
        X = np.array([[d["avg_rtt"], d["stddev"], d["jitter"]] for d in data]) # Extracting the relevant information from each d in data

        # Training the isolation forest model
        model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42) # model's parameters 
        model.fit(X) # train the model on the dataset X

        # Predict the anomalies
        predictions = model.predict(X) # 1 for normal, -1 for anomaly

        # Log the anomaly results onto InfluxDB
        for i, prediction in enumerate(predictions):
            if prediction == -1:
                anomaly_data = {
                    "ip": data[i]["ip"],
                    "timestamp": data[i]["timestamp"],
                    "avg_rtt": data[i]["avg_rtt"],
                    "stddev": data[i]["stddev"],
                    "jitter": data[i]["jitter"]
                }

                print(f"Anomaly detected for IP {data[i]['ip']}: {anomaly_data}")
                write_to_influxdb(anomaly_data, measurement="anomaly_metrics")

    except Exception as e:
        print(f"Error during anomaly detection: {e}")


# This function will log only the result.get() data from the ping_address function into JSON format file. This is just for local testing. Has no relevance to data logged onto InfluxDB
def log_results_to_file(results, filename="network_metrics.json"):
    try:
        # Read existing data. Create the file if isnt already created
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
    ip_list = ["8.8.8.8", "8.8.4.4", "1.1.1.1", "192.168.0.1"]  # Google, Cloudflare DNS and my Router's Ip

    # Use this part if you want to test your private router's metrics only
    #ip_list = ["192.168.0.1"]


    # Will continuously monitor the network
    while True:
        # Ping the IP addresses and get the results
        results = ping_addresses(ip_list)

        # Log the results to a file using the func created earlier
        log_results_to_file(results)

        # Detect anomalies in the results
        detect_anomalies(results)

        # Have a time interval of 30 seconds before the next ping
        time.sleep(30)

# Ensuring the function is only called when the script is running directly
if __name__ == "__main__":
    main() 
