import numpy as np
import pandas as pd
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from keras.models import Model
from keras.layers import Input, Dense
import json
from river import anomaly
from collections import defaultdict
from datetime import datetime, timedelta
from sklearn.cluster import DBSCAN
# import ollama
import groq  
import ZODB, ZODB.FileStorage
import transaction
from persistent.mapping import PersistentMapping
# import torch
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool, cpu_count, freeze_support
import os
import random

from dotenv import load_dotenv

load_dotenv()
groq_client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))

# -----------------------------
# Data Preprocessing
# -----------------------------

def read_data(db_path, key="logs"):
    """Generalized function to read data from ZODB based on the key provided."""
    storage = ZODB.FileStorage.FileStorage(db_path)
    db = ZODB.DB(storage)
    connection = db.open()
    root = connection.root()
    
    data = list(getattr(root, key, {}).values()) if hasattr(root, key) else []
    connection.close()
    db.close()
    return data

def extract_features(logs):
    operation_map = {"deletion": 0, "insertion": 1, "rename": 2, "update": 3}
    features, labels = [], []
    
    for log in logs:
        feature = []
        try:
            timestamp_obj = datetime.fromisoformat(log['timestamp'])    
            feature.extend([timestamp_obj.hour, timestamp_obj.day, timestamp_obj.weekday()])
        except ValueError:
            print(f"Failed to parse timestamp: {log['timestamp']}")
            feature.extend([0, 0, 0])  # Default values for invalid timestamps
        
        feature.append(operation_map.get(log['operation'], -1))  
        feature.append(hash(log['category']) % 1000)  
        feature.append(log.get('bytes_modified', 0))  
        feature.append(hash(log.get('new_name', '')) % 1000)  
        feature.append(hash(log.get('ip_address', '')) % 10000)
        feature.append(hash(log.get('mac_address', '')) % 10000)
        features.append(feature)
        labels.append(log['operation'])
    
    return np.array(features), np.array(labels)

# -----------------------------
# Models Initialization
# -----------------------------

def create_autoencoder(input_dim):
    input_layer = Input(shape=(input_dim,))
    encoded = Dense(64, activation='relu')(input_layer)
    decoded = Dense(input_dim, activation='sigmoid')(encoded)
    autoencoder = Model(input_layer, decoded)
    autoencoder.compile(optimizer='adam', loss='mean_squared_error')
    return autoencoder

def train_autoencoder(data):
    autoencoder = create_autoencoder(data.shape[1])
    autoencoder.fit(data, data, epochs=50, batch_size=64, validation_split=0.2, verbose=0)
    return autoencoder


recent_scores = []  
def dynamic_threshold(score, base_threshold=0.9, window_size=100):
    recent_scores.append(score)
    if len(recent_scores) > window_size:
        recent_scores.pop(0)

    if len(recent_scores) < 10:  
        return base_threshold

    mean_score = np.mean(recent_scores)
    std_score = np.std(recent_scores)

    dynamic_threshold_value = mean_score + 1.5 * std_score
    return max(base_threshold, dynamic_threshold_value)

from datetime import datetime

def calculate_risk(anomaly):
    """
    Calculates risk using a 3-factor model: Likelihood × Control Deficiency × Impact Score.
    """

    features = anomaly.get("features", {})
    anomaly_score = anomaly.get("anomaly_score", 0)  # Likelihood (0–1)

    operation = features.get("operation", "unknown")
    category = features.get("category", "Unknown")
    timestamp = features.get("timestamp")
    bytes_mod = abs(features.get("bytes_modified", 0))

    # --- Likelihood ---
    likelihood = max(0.0, min(1.0, anomaly_score))

    # --- Control Deficiency ---
    control_def = 0.4  # Default

    # Higher deficiency for sensitive file types
    sensitive_cats = {
        "Program executable": 0.9,
        "Configuration File": 0.8,
        "System Log": 0.7,
        "Backup": 0.7,
    }
    control_def = sensitive_cats.get(category, 0.4)

    # Add extra deficiency for risky operations
    if operation in ["deletion", "rename"]:
        control_def += 0.1

    # Unusual time (late night or early morning)
    if timestamp:
        try:
            hour = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S").hour
            if hour < 6 or hour > 22:
                control_def += 0.1
        except Exception:
            pass

    control_def = min(control_def, 1.0)  # Clamp to [0, 1]

    # --- Impact Score ---
    impact = 0.3  # Default

    if operation == "deletion":
        impact = 0.9
    elif operation == "update":
        if bytes_mod > 3000:
            impact = 0.85
        elif bytes_mod > 1000:
            impact = 0.6
        else:
            impact = 0.4
    elif operation == "rename":
        impact = 0.5
    elif operation == "insertion":
        impact = 0.3

    if anomaly.get("bulk_detected", False):
        impact += 0.1

    impact = min(impact, 1.0)

    # --- Final Risk Calculation ---
    raw_risk = likelihood * control_def * impact
    risk_score = round(raw_risk * 100, 2)  # Scale to 0–100

    return risk_score

def assign_risk_to_anomalies(anomalies):
    """
    Loops through detected anomalies and assigns a risk score to each.
    """
    for anomaly in anomalies:
        anomaly["risk_score"] = calculate_risk(anomaly)
    return anomalies

def detect_anomalies_with_halfspacetree_dynamic(data_scaled):
    river_model = anomaly.HalfSpaceTrees()
    data_river = [{f'feature_{i}': value for i, value in enumerate(row)} for row in data_scaled]

    anomalies = []
    scores = []
    window_size = 60  # Balanced window size
    min_samples = 35  # Balanced minimum samples
    
    # First pass: collect scores for initial calibration
    for i, x in enumerate(data_river[:min_samples]):
        score = river_model.score_one(x)
        river_model.learn_one(x)
        scores.append(score)
    
    # Calculate initial threshold parameters
    if scores:
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        base_threshold = mean_score + 1.75 * std_score  # Balanced threshold
    else:
        base_threshold = 0.82
    
    # Second pass: actual anomaly detection
    for i, x in enumerate(data_river):
        score = river_model.score_one(x)
        river_model.learn_one(x)
        scores.append(score)
        
        if len(scores) > window_size:
            scores.pop(0)
        
        # Dynamic threshold calculation
        if len(scores) >= min_samples:
            current_mean = np.mean(scores[-window_size:])
            current_std = np.std(scores[-window_size:])
            
            # Balanced exponential moving average
            alpha = 0.1  # Moderate smoothing factor
            base_threshold = (1 - alpha) * base_threshold + alpha * (current_mean + 1.75 * current_std)
            
            # Balanced percentile threshold
            percentile_92 = np.percentile(scores[-window_size:], 92)  # Using 92nd percentile
            threshold = max(base_threshold, percentile_92)
            
            # Balanced anomaly criteria
            z_score = (score - current_mean) / (current_std + 1e-10)
            
            # Either condition can trigger an anomaly, but with moderate thresholds
            if (z_score > 1.9) or (score > threshold and z_score > 1.5):
                # Moderate validation using recent history
                recent_scores = scores[-15:]  # Look at last 15 scores
                recent_mean = np.mean(recent_scores)
                recent_std = np.std(recent_scores)
                
                if score > recent_mean + 1.75 * recent_std:
                    anomalies.append({
                        "index": i,
                        "features": x,
                        "anomaly_score": score,
                        "threshold": threshold,
                        "method": "HalfSpaceTrees (Dynamic)"
                    })
    
    # Flexible post-processing
    target_count = np.mean([25, 30])  # Target around 25-30 anomalies
    if len(anomalies) > target_count * 1.2:  # Allow 20% over target
        anomalies.sort(key=lambda x: x['anomaly_score'], reverse=True)
        anomalies = anomalies[:int(target_count)]
    
    return anomalies

def adjust_weights(anomaly_counts):
    """Dynamically adjust model weights with balanced controls."""
    total_anomalies = sum(anomaly_counts.values())
    if total_anomalies == 0:
        return
    
    # Calculate average anomalies excluding RiverModel
    traditional_models = ['IsolationForest', 'OneClassSVM', 'LOF', 'Autoencoder']
    traditional_avg = np.mean([anomaly_counts[model] for model in traditional_models])
    
    # Set moderate target range
    target_min = traditional_avg * 0.8
    target_max = traditional_avg * 1.2
    
    # Adjust weights with moderate changes
    for model in weights.keys():
        if model == "RiverModel":
            count = anomaly_counts[model]
            if count > target_max:
                weights[model] = 0.8  # Moderate reduction
            elif count < target_min:
                weights[model] = 1.1  # Moderate increase
            else:
                weights[model] = 1.0
        else:
            weights[model] = 1.0
    
    # Normalize weights
    total_weight = sum(weights.values())
    for model in weights:
        weights[model] = weights[model] * len(weights) / total_weight 
# -----------------------------
# Anomaly Detection
# -----------------------------
weights = {
    "IsolationForest": 1.0,
    "OneClassSVM": 1.0,
    "LOF": 1.0,
    "Autoencoder": 1.0,
    "RiverModel": 1.0,
}

def dynamic_contamination(data):
    """Determine contamination dynamically based on data distribution."""
    error_scores = np.mean(data, axis=1)
    q75, q25 = np.percentile(error_scores, [75, 25])
    iqr_value = q75 - q25
    threshold = q75 + 1.5 * iqr_value
    return max(0.01, min(0.2, np.sum(error_scores > threshold) / len(error_scores)))


def detect_anomalies_with_scores(data):
    data = np.array(data)
    if len(data.shape) == 1:
        data = data.reshape(-1, 1) 

    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)

    contamination = dynamic_contamination(data_scaled)

    # 1. Isolation Forest
    isolation_forest = IsolationForest(contamination=contamination, random_state=42)
    isolation_forest.fit(data_scaled)
    score_iforest = isolation_forest.decision_function(data_scaled)
    predictions_iforest = isolation_forest.predict(data_scaled)
    count_iforest = np.sum(predictions_iforest == -1)

    # 2. One-Class SVM
    ocsvm = OneClassSVM(nu=contamination, kernel="rbf", gamma=0.1)
    ocsvm.fit(data_scaled)
    score_ocsvm = ocsvm.decision_function(data_scaled)
    predictions_ocsvm = ocsvm.predict(data_scaled)
    count_ocsvm = np.sum(predictions_ocsvm == -1)

    # 3. LOF
    lof = LocalOutlierFactor(n_neighbors=20, contamination=contamination)
    predictions_lof = lof.fit_predict(data_scaled)
    score_lof = -lof.negative_outlier_factor_
    count_lof = np.sum(predictions_lof == -1)

    # 4. Autoencoder
    autoencoder = train_autoencoder(data_scaled[:-1])  
    reconstruction_error = np.mean((data_scaled - autoencoder.predict(data_scaled))**2, axis=1)
    reconstruction_error = (reconstruction_error - np.min(reconstruction_error)) / (np.max(reconstruction_error) - np.min(reconstruction_error))

    # Use a dynamic threshold closer to other models
    threshold = np.percentile(reconstruction_error, 99)  # Instead of 95
    predictions_autoencoder = reconstruction_error > threshold
    count_autoencoder = np.sum(predictions_autoencoder)

    # 5. River Model
    anomalies_river = detect_anomalies_with_halfspacetree_dynamic(data_scaled)
    count_river = len(anomalies_river)

    # Store anomaly counts per model
    anomaly_counts = {
        "IsolationForest": count_iforest,
        "OneClassSVM": count_ocsvm,
        "LOF": count_lof,
        "Autoencoder": count_autoencoder,
        "RiverModel": count_river,
    }

    scores = {
        "IsolationForest": score_iforest,
        "OneClassSVM": score_ocsvm,
        "LOF": score_lof,
        "Autoencoder": reconstruction_error,
        "RiverModel": [anomaly['anomaly_score'] for anomaly in anomalies_river],
    }
    predictions = {
        "IsolationForest": predictions_iforest,
        "OneClassSVM": predictions_ocsvm,
        "LOF": predictions_lof,
        "Autoencoder": predictions_autoencoder,
        "RiverModel": [1 if anomaly['anomaly_score'] > anomaly['threshold'] else 0 for anomaly in anomalies_river],
    }
    
    adjust_weights(anomaly_counts)
    
    max_length = len(data_scaled)  # Ensuring all predictions match dataset length

    for model in predictions.keys():
        predictions[model] = np.array(predictions[model])

        # If a model returns fewer predictions, pad with zeros (normal behavior assumption)
        if len(predictions[model]) < max_length:
            predictions[model] = np.pad(predictions[model], (0, max_length - len(predictions[model])), mode='constant')

    # Stack predictions and compute final anomalies
    final_anomalies = np.mean(np.vstack(list(predictions.values())), axis=0) > 0.5

    anomalies_with_risk = assign_risk_to_anomalies(anomalies_river)

    return scores, predictions, anomaly_counts, final_anomalies, weights, anomalies_with_risk

# -----------------------------
# Model Aggregation
# -----------------------------

def combine_anomaly_scores(scores, weights, threshold=0.5):
    """
    Combines anomaly scores using weighted average and classifies based on threshold.
    Ensures that the scores from each model have the same length.
    """
    max_length = max(len(scores[model]) for model in scores)

    aggregated_score = np.zeros(max_length, dtype=float)

    for model, weight in weights.items():
        model_scores = np.array(scores[model], dtype=float)

        if len(model_scores) < max_length:
            padding = np.zeros(max_length - len(model_scores))
            model_scores = np.concatenate([model_scores, padding])

        aggregated_score += model_scores * weight

    aggregated_score = (aggregated_score - np.min(aggregated_score)) / (np.max(aggregated_score) - np.min(aggregated_score))

    return aggregated_score > threshold, aggregated_score


# -----------------------------
# Save Anomaly flagged logs (Generalized)
# -----------------------------

from collections import defaultdict
import json

def save_anomalies_sequentially(logs, predictions, db_path="anomalies.fs"):
    """
    Saves anomalies in a sequential order without grouping by operation.
    """
    storage = ZODB.FileStorage.FileStorage(db_path)
    db = ZODB.DB(storage)
    connection = db.open()
    root = connection.root()
    
    if not hasattr(root, 'anomalies_sequential'):
        root.anomalies_sequential = PersistentMapping()
    
    anomalies = []
    for model, pred in predictions.items():
        for log, pred_value in zip(logs, pred):
            if pred_value == -1:
                anomalies.append({"model": model, "log": log})
    
    root.anomalies_sequential.update({i: anomalies[i] for i in range(len(anomalies))})
    transaction.commit()
    
    connection.close()
    db.close()
    print(f"Saved anomalies sequentially to {db_path}")

# ---------------------------------------
# Anomaly Detection for each operation (Pipeline)
# ---------------------------------------

def save_anomalies_by_operation(logs, predictions, file_path="anomalies_by_operation.json"):
    """
    Saves anomalies grouped by operation type to a JSON file.
    """
    # Dictionary to store anomalies per operation
    anomalies_by_operation = defaultdict(lambda: {"anomaly_count": 0, "logs": []})
    # Iterate over each model's predictions
    for model, pred in predictions.items():
        for log, pred_value in zip(logs, pred):
            if pred_value == -1:  # Anomaly detected
                operation = log.get("operation", "unknown")  # Ensure operation field exists
                anomalies_by_operation[operation]["logs"].append({"model": model, "log": log})
                anomalies_by_operation[operation]["anomaly_count"] += 1

    # Save the results
    with open(file_path, 'w') as f:
        json.dump(anomalies_by_operation, f, indent=4)
    
    print(f"Saved anomalies by operation to {file_path}")


# -----------------------------
# Anomaly File with reason to each
# -----------------------------


def extract_features_anomaly(log):
    """Extracts feature vector from a log entry."""
    operation_map = {"deletion": 0, "insertion": 1, "rename": 2, "update": 3}
    
    file_path = log["log"]["file"]
    operation = log["log"]["operation"]
    timestamp = log["log"]["timestamp"]
    category = log["log"]["category"]
    
    bytes_modified = log["log"].get("bytes_modified", 0)
    new_name = log["log"].get("new_name", None)
    ip_address = log["log"].get("ip_address", "")
    
    mac_address = log["log"].get("mac_address", "")
    
    operation_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
    hour = operation_time.hour
    weekday = operation_time.weekday()
    
    operation_code = operation_map.get(operation, -1)
    category_hash = hash(category) % 1000
    new_name_hash = hash(new_name) % 1000 if new_name else 0
    ip_hash = hash(ip_address) % 10000
    mac_hash = hash(mac_address) % 10000
    
    return [hour, weekday, operation_code, category_hash, bytes_modified, new_name_hash, ip_hash, mac_hash], log

# print("Updated feature extraction to include IP and MAC address attributes.")

def process_log(idx, anomaly_logs, cluster_labels, mean_operation_times, llm_responses):
    """Processes a single log entry and generates anomaly reasons."""
    entry = anomaly_logs[idx]
    file_path = entry["log"]["file"]
    operation = entry["log"]["operation"]
    timestamp = entry["log"]["timestamp"]
    category = entry["log"]["category"]
    bytes_modified = entry["log"].get("bytes_modified", 0)
    ip_address = entry["log"].get("ip_address", "")
    
    mac_address = entry["log"].get("mac_address", "")
    print(ip_address + "----- " + mac_address)
    if(ip_address and mac_address):
        reasons = []
        cluster_id = cluster_labels[idx]

        if cluster_id == -1:
            reasons.append("This anomaly is highly unique compared to detected patterns.")
        else:
            reasons.append(f"This anomaly belongs to a detected pattern (Cluster {cluster_id}).")

        avg_op_time = mean_operation_times.get(operation, None)
        operation_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S").hour
        if avg_op_time and abs(operation_time - avg_op_time) > 5:
            reasons.append(f"Unusual operation time: {operation_time} vs avg {avg_op_time:.1f}.")

        if bytes_modified > 10**6:
            reasons.append("Large file modification detected.")

        risk_score = calculate_risk(entry)
        reasons.append(f"Anomaly detected from IP: {ip_address}, MAC: {mac_address}.")
        # LLM-based reasoning (only if needed)
        if cluster_id not in llm_responses:
            llm_prompt = (
                "You are a cybersecurity expert specializing in anomaly detection. "
                "Analyze the following log entry and provide a concise 2-3 line explanation "
                "for why it may be considered an anomaly.\n\n"
                "## Log Entry Details:\n"
                f"- **Cluster ID**: {cluster_id} (If -1, it is highly unique.)\n"
                f"- **Operation**: {operation}\n"
                f"- **File Category**: {category}\n"
                f"- **Timestamp**: {timestamp}\n"
                f"- **Bytes Modified**: {bytes_modified}\n"
                f"- **File Path**: {file_path}\n"
                f"- **IP Address**: {ip_address}\n"
                f"- **MAC Address**: {mac_address}\n\n"
                "### Response Instructions:\n"
                "- Strictly limit response to **2-3 lines**.\n"
                "- Clearly state why this log is suspicious.\n"
                "- Mention if it requires further investigation or immediate action."
            )
            try:
                response = groq_client.chat.completions.create(
                    model="gemma2-9b-it", 
                    messages=[{"role": "system", "content": llm_prompt}]
                )
                llm_responses[cluster_id] = response.choices[0].message.content.strip()
            except Exception as e:
                llm_responses[cluster_id] = f"LLM explanation failed: {str(e)}"

        reasons.append(llm_responses[cluster_id])
    
        return {
            "file": file_path,
            "operation": operation,
            "timestamp": timestamp,
            "category": category,
            "risk_score": risk_score,
            "ip_address": ip_address,
            "mac_address": mac_address,
            "reasons": reasons
        }

def explain_anomalies(db_path):
    freeze_support()  
    logs = read_data(db_path, key="anomalies_sequential")
    
    with Pool(cpu_count()) as pool:
        feature_vectors, anomaly_logs = zip(*pool.map(extract_features_anomaly, logs))
    
    clustering = DBSCAN(eps=3, min_samples=2).fit(feature_vectors)
    cluster_labels = clustering.labels_
    
    operation_times = defaultdict(list)
    for entry in logs:
        op = entry["log"]["operation"]
        operation_times[op].append(datetime.strptime(entry["log"]["timestamp"], "%Y-%m-%dT%H:%M:%S").hour)
    mean_operation_times = {op: np.mean(hours) for op, hours in operation_times.items()}
    
    anomaly_reasons = {"anomaly_count": len(logs), "logs": []}
    llm_responses = {}
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        anomaly_reasons["logs"] = list(executor.map(
            lambda idx: process_log(idx, anomaly_logs, cluster_labels, mean_operation_times, llm_responses), 
            range(len(anomaly_logs))
        ))
    print("Anomaly reasons: ", anomaly_reasons)

    print("Anomaly explanation completed.")
    return anomaly_reasons

