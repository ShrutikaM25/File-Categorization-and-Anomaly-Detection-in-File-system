import os
import json
import numpy as np
import pandas as pd
from anomaly import (
    detect_anomalies_with_scores,
    combine_anomaly_scores,
    extract_features_from_log,
    save_anomalies_by_operation,
    save_anomalies_sequentially,
    explain_anomalies
)

# -----------------------------
# Locate Drive Logs
# -----------------------------

def get_drive_log_files():

    log_dir = os.path.join(os.path.expanduser("~"), "Documents", "DriveLogs")
    if not os.path.exists(log_dir):
        print(f"Log directory not found: {log_dir}")
        return []
    
    log_files = [
        os.path.join(log_dir, file)
        for file in os.listdir(log_dir)
        if file.endswith("_drive_operations_log.json")
    ]
    
    print(f"Found log files: {log_files}")
    return log_files

# -----------------------------
# Read and Merge Logs
# -----------------------------

def read_logs(file_path):
    """Reads a JSON log file, handling errors gracefully."""
    try:
        with open(file_path, 'r') as f:
            logs = [json.loads(line) for line in f]  # Read line by line
        return logs
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading {file_path}: {e}")
        return []

def merge_logs(log_files):
    """Combines logs from multiple files into a single list."""
    all_logs = []
    for file in log_files:
        logs = read_logs(file)
        all_logs.extend(logs)
    return all_logs

# -----------------------------
# Main Execution
# -----------------------------

log_files = get_drive_log_files()
if not log_files:
    print("No drive log files found. Exiting.")
    exit()

logs = merge_logs(log_files)

# Extract features
features, labels = extract_features_from_log(logs)

# Detect anomalies
scores, predictions, anomaly_counts, final_anomalies, updated_weights = detect_anomalies_with_scores(features)

# Combine anomaly scores
combined_predictions, aggregated_scores = combine_anomaly_scores(scores, updated_weights)

# Save anomalies
save_anomalies_sequentially(logs, predictions, file_path="anomalies_sequential.json")
save_anomalies_by_operation(logs, predictions, "anomalies_by_operations.json")

print("Anomalies saved successfully!")

with open("anomalies_sequential.json", "r") as file:
    anomaly_logs = json.load(file)

# Run explainability module
anomaly_reasons = explain_anomalies(anomaly_logs)

# Save the final explained anomalies
output_file = "optimized_anomalies.json"
with open(output_file, "w") as json_file:
    json.dump(anomaly_reasons, json_file, indent=4)

print("Explainable anomaly detection completed and saved.")