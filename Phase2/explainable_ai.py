from collections import defaultdict
from sklearn.cluster import DBSCAN
import numpy as np
from datetime import datetime
# import json
import unqlite
# import groq
import ollama  
# import torch
import os
import time
# from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool, cpu_count, freeze_support

# load_dotenv()
# groq_client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))

def extract_features(log):
    """Extracts feature vector from a log entry."""
    operation_map = {"delete": 0, "insert": 1, "rename": 2, "update": 3}
    
    file_path = log["log"]["file"]
    operation = log["log"]["operation"]
    timestamp = log["log"]["timestamp"]
    category = log["log"]["category"]
    
    bytes_modified = log["log"].get("bytes_modified", 0)
    new_name = log["log"].get("new_name", None)
    
    operation_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
    hour = operation_time.hour
    weekday = operation_time.weekday()
    
    operation_code = operation_map.get(operation, -1)
    category_hash = hash(category) % 1000
    new_name_hash = hash(new_name) % 1000 if new_name else 0
    
    return [hour, weekday, operation_code, category_hash, bytes_modified, new_name_hash], log

def process_log(idx, anomaly_logs, cluster_labels, mean_operation_times, llm_responses):
    """Processes a single log entry and generates anomaly reasons."""
    entry = anomaly_logs[idx]
    file_path = entry["log"]["file"]
    operation = entry["log"]["operation"]
    timestamp = entry["log"]["timestamp"]
    category = entry["log"]["category"]
    bytes_modified = entry["log"].get("bytes_modified", 0)

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

    # LLM-based reasoning (only if needed)
    if cluster_id not in llm_responses:
        llm_prompt = (
            "You are an expert in anomaly detection. Analyze the following log entry.\n"
            f"Cluster ID: {cluster_id}. If -1, it's unique.\n"
            f"Log Entry: {entry}"
        )
        try:
            # use_gpu = torch.cuda.is_available()
            # model_name = "mixtral" if use_gpu else "mistral"
            
            response = ollama.chat(
                model="llama3",  
                messages=[{"role": "system", "content": llm_prompt}]
            )
            llm_responses[cluster_id] = response["message"]["content"].strip()
        except Exception as e:
            llm_responses[cluster_id] = f"LLM explanation failed: {str(e)}"

    reasons.append(llm_responses[cluster_id])
    
    return {
        "file": file_path,
        "operation": operation,
        "timestamp": timestamp,
        "category": category,
        "reasons": reasons
    }

if __name__ == "__main__":
    freeze_support()  
    
    db = unqlite.UnQLite("anomalies.db")  # Initialize UnQLite database
    logs = list(db.collection("logs").all())

    # Parallel Feature Extraction
    start_time = time.time()
    with Pool(processes=cpu_count()) as pool:
        results = pool.map(extract_features, logs)

    feature_vectors, anomaly_logs = zip(*results)
    feature_extraction_time = time.time() - start_time
    print(f"Feature extraction time (parallel): {feature_extraction_time:.4f} seconds")

    # Clustering
    start_time = time.time()
    clustering = DBSCAN(eps=3, min_samples=2).fit(feature_vectors)
    cluster_labels = clustering.labels_
    clustering_time = time.time() - start_time
    print(f"Clustering time: {clustering_time:.4f} seconds")

    # Statistical analysis
    start_time = time.time()
    operation_times = defaultdict(list)
    for entry in logs:
        op = entry["log"]["operation"]
        ts = datetime.strptime(entry["log"]["timestamp"], "%Y-%m-%dT%H:%M:%S")
        operation_times[op].append(ts.hour)

    mean_operation_times = {op: np.mean(hours) for op, hours in operation_times.items()}
    statistical_analysis_time = time.time() - start_time
    print(f"Statistical analysis time: {statistical_analysis_time:.4f} seconds")

    # Step 3: Generate anomaly reasons using Parallel LLM Processing
    anomaly_reasons = {"anomaly_count": len(logs), "logs": []}
    llm_responses = {}

    start_time = time.time()
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(
            lambda idx: process_log(idx, anomaly_logs, cluster_labels, mean_operation_times, llm_responses), 
            range(len(anomaly_logs))
        ))
    llm_total_time = time.time() - start_time
    print(f"LLM processing time (parallel): {llm_total_time:.4f} seconds")

    anomaly_reasons["logs"] = results

    # Save results
    db.collection("anomaly_results").store(anomaly_reasons)

    print("Optimized anomaly detection completed and saved.")
